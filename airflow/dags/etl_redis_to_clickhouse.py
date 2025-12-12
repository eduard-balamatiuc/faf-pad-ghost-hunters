"""
ETL DAG: Redis to ClickHouse Data Warehouse

Extracts data from Redis databases and loads into ClickHouse.
Creates point-in-time snapshots of Redis keys for historical analysis.

Schedule: Hourly (Redis data changes frequently)
Strategy: Snapshot append (each run creates a new snapshot)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import csv
import io

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

from config.databases import REDIS_CONFIGS, CLICKHOUSE_CONFIG
from connectors.redis_connector import RedisConnector
from connectors.clickhouse import ClickHouseConnector

logger = logging.getLogger(__name__)

# Default DAG arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}


def redis_data_to_csv(records: List[Dict], snapshot_time: str, service_name: str) -> bytes:
    """Convert Redis records to CSV format for ClickHouse."""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    for record in records:
        row = [
            service_name,
            record.get('key', ''),
            record.get('type', ''),
            record.get('value') if record.get('value') is not None else '\\N',
            str(record.get('ttl')) if record.get('ttl') is not None else '\\N',
            snapshot_time,
        ]
        writer.writerow(row)

    return output.getvalue().encode('utf-8')


def get_existing_key_values(ch: ClickHouseConnector, table_name: str) -> set:
    """Get existing (key, value) pairs from ClickHouse to detect exact duplicates."""
    try:
        query = f"SELECT DISTINCT `key`, `value` FROM {table_name}"
        result = ch.execute_query(query)
        pairs = set()
        if result:
            for row in result.split('\n'):
                if row.strip():
                    # Tab-separated key and value
                    parts = row.split('\t', 1)
                    if len(parts) >= 2:
                        pairs.add((parts[0], parts[1]))
                    elif len(parts) == 1:
                        pairs.add((parts[0], ''))
        return pairs
    except Exception as e:
        logger.warning(f"Could not fetch existing key-values from {table_name}: {e}")
        return set()


def etl_redis_service(service_name: str, **kwargs) -> Dict[str, Any]:
    """
    ETL function for a Redis service with incremental loading.
    Stacks up records like logs, but skips exact duplicates (same key AND value).

    Args:
        service_name: Name of the service to process

    Returns:
        Dictionary with ETL statistics
    """
    config = REDIS_CONFIGS.get(service_name)
    if not config:
        raise ValueError(f"Unknown Redis service: {service_name}")

    logger.info(f"Starting Redis ETL for service: {service_name}")

    # Initialize connectors
    redis_conn = RedisConnector(config)
    ch = ClickHouseConnector(CLICKHOUSE_CONFIG)

    # Test connections
    if not redis_conn.test_connection():
        raise Exception(f"Cannot connect to Redis for {service_name}")

    if not ch.test_connection():
        raise Exception("Cannot connect to ClickHouse")

    # Ensure database exists
    ch.ensure_database()

    stats = {
        'service': service_name,
        'keys_extracted': 0,
        'skipped_duplicates': 0,
        'errors': [],
    }

    try:
        # Table name for Redis snapshots
        ch_table_name = f"redis_{service_name}_snapshot"
        snapshot_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        # Create ClickHouse table if not exists
        columns = [
            ('service', 'String'),
            ('key', 'String'),
            ('type', 'String'),
            ('value', 'Nullable(String)'),
            ('ttl', 'Nullable(Int64)'),
            ('snapshot_time', 'DateTime'),
        ]

        ch.create_table(
            ch_table_name,
            columns,
            order_by=['service', 'key', 'snapshot_time'],
            engine='MergeTree'  # Append-only, keeps history
        )

        # Get existing (key, value) pairs to skip exact duplicates
        existing_pairs = set()
        if ch.table_exists(ch_table_name):
            existing_pairs = get_existing_key_values(ch, ch_table_name)
            logger.info(f"Found {len(existing_pairs)} existing key-value pairs in {ch_table_name}")

        # Extract all data from Redis
        records = redis_conn.extract_all_data()
        logger.info(f"Extracted {len(records)} keys from {service_name}")

        if records:
            # Filter out exact duplicates (same key AND same value)
            original_count = len(records)
            new_records = []
            for r in records:
                key = r.get('key', '')
                value = r.get('value') if r.get('value') is not None else '\\N'
                if (key, value) not in existing_pairs:
                    new_records.append(r)

            stats['skipped_duplicates'] = original_count - len(new_records)

            if new_records:
                # Convert to CSV
                csv_data = redis_data_to_csv(new_records, snapshot_time, service_name)

                # Insert into ClickHouse
                ch.insert_data(
                    ch_table_name,
                    ['service', 'key', 'type', 'value', 'ttl', 'snapshot_time'],
                    csv_data
                )

                stats['keys_extracted'] = len(new_records)
                logger.info(f"Inserted {len(new_records)} new records, skipped {stats['skipped_duplicates']} duplicates")
            else:
                logger.info(f"All records are duplicates, nothing new to insert")
        else:
            logger.info(f"No keys found in {service_name}")

    except Exception as e:
        error_msg = f"Error processing {service_name}: {str(e)}"
        logger.error(error_msg)
        stats['errors'].append(error_msg)
    finally:
        redis_conn.close()

    return stats


def generate_summary(**kwargs) -> None:
    """Generate summary of all Redis ETL operations."""
    ti = kwargs['ti']

    logger.info("=" * 60)
    logger.info("REDIS ETL SUMMARY (Incremental)")
    logger.info("=" * 60)

    total_keys = 0
    total_skipped = 0
    total_errors = 0

    for service_name in REDIS_CONFIGS.keys():
        try:
            stats = ti.xcom_pull(task_ids=f'etl_{service_name}')
            if stats:
                keys = stats.get('keys_extracted', 0)
                skipped = stats.get('skipped_duplicates', 0)
                errors = len(stats.get('errors', []))
                total_keys += keys
                total_skipped += skipped
                total_errors += errors

                status = 'OK' if errors == 0 else f'WARN ({errors} errors)'
                logger.info(f"  {service_name}: {keys} new, {skipped} skipped - {status}")

                for error in stats.get('errors', []):
                    logger.warning(f"    - {error}")
        except Exception as e:
            logger.error(f"  {service_name}: Failed to get stats - {e}")

    logger.info("-" * 60)
    logger.info(f"TOTAL: {total_keys} new keys, {total_skipped} duplicates skipped")
    if total_errors > 0:
        logger.warning(f"Errors encountered: {total_errors}")
    logger.info("=" * 60)


# Create the DAG
with DAG(
    'etl_redis_to_clickhouse',
    default_args=default_args,
    description='ETL pipeline from Redis to ClickHouse (hourly snapshots)',
    schedule_interval='@hourly',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['etl', 'redis', 'clickhouse', 'warehouse'],
) as dag:

    start = EmptyOperator(task_id='start')
    end = EmptyOperator(task_id='end')

    # Create ETL tasks for each Redis service
    etl_tasks = []
    for service_name in REDIS_CONFIGS.keys():
        task = PythonOperator(
            task_id=f'etl_{service_name}',
            python_callable=etl_redis_service,
            op_kwargs={'service_name': service_name},
        )
        etl_tasks.append(task)

    # Summary task
    summary_task = PythonOperator(
        task_id='generate_summary',
        python_callable=generate_summary,
    )

    # Set task dependencies
    start >> etl_tasks >> summary_task >> end
