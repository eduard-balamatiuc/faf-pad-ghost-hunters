"""
ETL DAG: MongoDB to ClickHouse Data Warehouse

Extracts data from MongoDB databases (chat service) and loads into ClickHouse.
Tables are prefixed with 'mongo_' followed by service name (e.g., mongo_chat_messages)

Schedule: Daily at midnight
Strategy: Incremental append with deduplication (no overwrites)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Set

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

from config.databases import MONGO_CONFIGS, CLICKHOUSE_CONFIG
from connectors.mongodb import MongoDBConnector
from connectors.clickhouse import ClickHouseConnector
from utils.type_mappings import map_mongo_type_to_ch

logger = logging.getLogger(__name__)

# Collections to skip during ETL
SKIP_COLLECTIONS = {
    'system.indexes',
    'system.users',
}

# Default DAG arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}


def mongo_docs_to_csv(documents: list, field_names: list) -> bytes:
    """Convert MongoDB documents to CSV format for ClickHouse."""
    import csv
    import io
    import json
    from datetime import datetime as dt

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    for doc in documents:
        row = []
        for field in field_names:
            val = doc.get(field)
            if val is None:
                row.append('\\N')
            elif isinstance(val, bool):
                row.append('1' if val else '0')
            elif isinstance(val, dt):
                row.append(val.strftime('%Y-%m-%d %H:%M:%S'))
            elif isinstance(val, (list, dict)):
                row.append(json.dumps(val))
            else:
                row.append(str(val))
        writer.writerow(row)

    csv_data = output.getvalue()
    output.close()
    return csv_data.encode('utf-8')


def get_existing_ids(ch: ClickHouseConnector, table_name: str, id_field: str = '_id') -> Set[str]:
    """
    Get set of existing IDs from ClickHouse table.

    Args:
        ch: ClickHouse connector
        table_name: Name of the table
        id_field: Name of the ID field

    Returns:
        Set of existing IDs
    """
    try:
        query = f"SELECT `{id_field}` FROM {table_name}"
        result = ch.execute_query(query)
        if result:
            return set(row.strip() for row in result.split('\n') if row.strip())
        return set()
    except Exception as e:
        logger.warning(f"Could not fetch existing IDs from {table_name}: {e}")
        return set()


def etl_mongo_service(service_name: str, **kwargs) -> Dict[str, Any]:
    """
    ETL function for a MongoDB service with incremental loading.
    Only inserts new records, skips duplicates based on _id.

    Args:
        service_name: Name of the service to process

    Returns:
        Dictionary with ETL statistics
    """
    config = MONGO_CONFIGS.get(service_name)
    if not config:
        raise ValueError(f"Unknown MongoDB service: {service_name}")

    logger.info(f"Starting MongoDB ETL for service: {service_name}")

    # Initialize connectors
    mongo = MongoDBConnector(config)
    ch = ClickHouseConnector(CLICKHOUSE_CONFIG)

    # Test connections
    if not mongo.test_connection():
        raise Exception(f"Cannot connect to MongoDB for {service_name}")

    if not ch.test_connection():
        raise Exception("Cannot connect to ClickHouse")

    # Ensure database exists
    ch.ensure_database()

    # Get collections from MongoDB
    collections = mongo.get_collections()
    collections = [c for c in collections if c not in SKIP_COLLECTIONS]

    logger.info(f"Found {len(collections)} collections in {service_name}: {collections}")

    stats = {
        'service': service_name,
        'collections_processed': 0,
        'new_rows': 0,
        'skipped_duplicates': 0,
        'errors': [],
    }

    for collection_name in collections:
        try:
            ch_table_name = f"mongo_{service_name}_{collection_name}"
            logger.info(f"Processing: {service_name}.{collection_name} -> {ch_table_name}")

            # Get schema from MongoDB (by sampling documents)
            mongo_schema = mongo.get_collection_schema(collection_name)

            if not mongo_schema:
                logger.info(f"No schema found for {collection_name}, skipping")
                continue

            # Map to ClickHouse types
            ch_columns = [
                (field_name, map_mongo_type_to_ch(field_type, is_nullable=True))
                for field_name, field_type in mongo_schema
            ]

            # Use _id as primary key if present
            has_id = any(f[0] == '_id' for f in mongo_schema)
            order_by = ['_id'] if has_id else None

            # Create ClickHouse table if not exists (won't drop existing)
            ch.create_table(ch_table_name, ch_columns, order_by=order_by)

            # Get existing IDs to avoid duplicates
            existing_ids = set()
            if has_id and ch.table_exists(ch_table_name):
                existing_ids = get_existing_ids(ch, ch_table_name, '_id')
                logger.info(f"Found {len(existing_ids)} existing records in {ch_table_name}")

            # Extract data from MongoDB
            field_names, documents = mongo.extract_data(collection_name)

            if documents:
                # Filter out duplicates
                if has_id and existing_ids:
                    original_count = len(documents)
                    documents = [
                        doc for doc in documents
                        if str(doc.get('_id', '')) not in existing_ids
                    ]
                    skipped = original_count - len(documents)
                    stats['skipped_duplicates'] += skipped
                    if skipped > 0:
                        logger.info(f"Skipped {skipped} duplicate documents")

                if documents:
                    # Transform and load new documents to ClickHouse
                    csv_data = mongo_docs_to_csv(documents, field_names)
                    ch.insert_data(ch_table_name, field_names, csv_data)

                    stats['new_rows'] += len(documents)
                    logger.info(f"Inserted {len(documents)} new documents into {ch_table_name}")
                else:
                    logger.info(f"No new documents to insert for {collection_name}")
            else:
                logger.info(f"No data in {collection_name}")

            stats['collections_processed'] += 1

        except Exception as e:
            error_msg = f"Error processing {collection_name}: {str(e)}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)

    # Close MongoDB connection
    mongo.close()

    logger.info(
        f"MongoDB ETL completed for {service_name}: "
        f"{stats['collections_processed']} collections, "
        f"{stats['new_rows']} new documents, "
        f"{stats['skipped_duplicates']} duplicates skipped"
    )
    return stats


def generate_summary(**kwargs) -> None:
    """Generate and log ETL summary."""
    ti = kwargs['ti']

    logger.info("=" * 60)
    logger.info("MONGODB ETL SUMMARY (Incremental)")
    logger.info("=" * 60)

    total_collections = 0
    total_new = 0
    total_skipped = 0
    all_errors = []

    for service in MONGO_CONFIGS.keys():
        try:
            result = ti.xcom_pull(task_ids=f'etl_mongo_{service}')
            if result:
                collections = result.get('collections_processed', 0)
                new_rows = result.get('new_rows', 0)
                skipped = result.get('skipped_duplicates', 0)
                errors = result.get('errors', [])

                total_collections += collections
                total_new += new_rows
                total_skipped += skipped
                all_errors.extend(errors)

                status = "OK" if not errors else f"WARN ({len(errors)} errors)"
                logger.info(
                    f"  {service}: {collections} collections, "
                    f"{new_rows} new, {skipped} skipped - {status}"
                )
        except Exception as e:
            logger.error(f"  {service}: Failed to get results - {e}")

    logger.info("-" * 60)
    logger.info(f"TOTAL: {total_collections} collections, {total_new} new documents, {total_skipped} duplicates skipped")

    if all_errors:
        logger.warning(f"Errors encountered: {len(all_errors)}")
        for error in all_errors[:10]:
            logger.warning(f"  - {error}")

    logger.info("=" * 60)


# Create the DAG
with DAG(
    'etl_mongo_to_clickhouse',
    default_args=default_args,
    description='ETL pipeline: MongoDB -> ClickHouse (incremental, no overwrites)',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['etl', 'mongodb', 'clickhouse', 'warehouse', 'incremental'],
    doc_md=__doc__,
) as dag:

    # Start
    start = EmptyOperator(task_id='start')

    # ETL tasks for each MongoDB service
    etl_tasks = []
    for service_name in MONGO_CONFIGS.keys():
        task = PythonOperator(
            task_id=f'etl_mongo_{service_name}',
            python_callable=etl_mongo_service,
            op_kwargs={'service_name': service_name},
        )
        etl_tasks.append(task)

    # Summary
    summary = PythonOperator(
        task_id='generate_summary',
        python_callable=generate_summary,
        trigger_rule='all_done',
    )

    # End
    end = EmptyOperator(task_id='end')

    # Task dependencies
    start >> etl_tasks >> summary >> end
