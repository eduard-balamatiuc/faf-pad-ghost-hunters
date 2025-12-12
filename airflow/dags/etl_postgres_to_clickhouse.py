"""
ETL DAG: PostgreSQL to ClickHouse Data Warehouse

Extracts data from all service PostgreSQL databases and loads into ClickHouse.
Tables are organized by service prefix (e.g., user_mgmt_, inventory_, ghost_, shop_)

Schedule: Daily at midnight
Strategy: Full refresh (truncate and reload)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator

from config.databases import DB_CONFIGS, CLICKHOUSE_CONFIG
from connectors.postgres import PostgresConnector
from connectors.clickhouse import ClickHouseConnector
from utils.type_mappings import map_pg_type_to_ch
from utils.data_transformers import rows_to_csv

logger = logging.getLogger(__name__)

# Tables to skip during ETL
SKIP_TABLES = {
    'schema_migrations',
    'ar_internal_metadata',
    'flyway_schema_history',
    'alembic_version',
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


def init_clickhouse(**kwargs) -> None:
    """Initialize ClickHouse database."""
    ch = ClickHouseConnector(CLICKHOUSE_CONFIG)
    ch.ensure_database()
    logger.info("ClickHouse initialization completed")


def etl_service(service_name: str, **kwargs) -> Dict[str, Any]:
    """
    ETL function for a single service.

    Args:
        service_name: Name of the service to process

    Returns:
        Dictionary with ETL statistics
    """
    config = DB_CONFIGS.get(service_name)
    if not config:
        raise ValueError(f"Unknown service: {service_name}")

    logger.info(f"Starting ETL for service: {service_name}")

    # Initialize connectors
    pg = PostgresConnector(config)
    ch = ClickHouseConnector(CLICKHOUSE_CONFIG)

    # Test connections
    if not pg.test_connection():
        raise Exception(f"Cannot connect to PostgreSQL for {service_name}")

    if not ch.test_connection():
        raise Exception("Cannot connect to ClickHouse")

    # Get tables from PostgreSQL
    tables = pg.get_tables()
    tables = [t for t in tables if t not in SKIP_TABLES and not t.startswith('_')]

    logger.info(f"Found {len(tables)} tables in {service_name}: {tables}")

    stats = {
        'service': service_name,
        'tables_processed': 0,
        'total_rows': 0,
        'errors': [],
    }

    for table_name in tables:
        try:
            ch_table_name = f"{service_name}_{table_name}"
            logger.info(f"Processing: {service_name}.{table_name} -> {ch_table_name}")

            # Get schema from PostgreSQL
            pg_schema = pg.get_table_schema(table_name)

            # Map to ClickHouse types
            ch_columns = [
                (col_name, map_pg_type_to_ch(data_type, is_nullable == 'YES'))
                for col_name, data_type, is_nullable in pg_schema
            ]

            # Get primary keys for ORDER BY
            pk_columns = pg.get_primary_keys(table_name)

            # Create ClickHouse table
            ch.create_table(ch_table_name, ch_columns, order_by=pk_columns or None)

            # Truncate for full refresh
            ch.truncate_table(ch_table_name)

            # Extract data from PostgreSQL
            col_names, rows = pg.extract_data(table_name)

            if rows:
                # Transform and load to ClickHouse
                csv_data = rows_to_csv(rows)
                ch.insert_data(ch_table_name, col_names, csv_data)

                stats['total_rows'] += len(rows)
                logger.info(f"Loaded {len(rows)} rows into {ch_table_name}")
            else:
                logger.info(f"No data in {table_name}")

            stats['tables_processed'] += 1

        except Exception as e:
            error_msg = f"Error processing {table_name}: {str(e)}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)

    logger.info(f"ETL completed for {service_name}: {stats['tables_processed']} tables, {stats['total_rows']} rows")
    return stats


def generate_summary(**kwargs) -> None:
    """Generate and log ETL summary."""
    ti = kwargs['ti']

    logger.info("=" * 60)
    logger.info("ETL SUMMARY")
    logger.info("=" * 60)

    total_tables = 0
    total_rows = 0
    all_errors = []

    for service in DB_CONFIGS.keys():
        try:
            result = ti.xcom_pull(task_ids=f'etl_{service}')
            if result:
                tables = result.get('tables_processed', 0)
                rows = result.get('total_rows', 0)
                errors = result.get('errors', [])

                total_tables += tables
                total_rows += rows
                all_errors.extend(errors)

                status = "OK" if not errors else f"WARN ({len(errors)} errors)"
                logger.info(f"  {service}: {tables} tables, {rows} rows - {status}")
        except Exception as e:
            logger.error(f"  {service}: Failed to get results - {e}")

    logger.info("-" * 60)
    logger.info(f"TOTAL: {total_tables} tables, {total_rows} rows")

    if all_errors:
        logger.warning(f"Errors encountered: {len(all_errors)}")
        for error in all_errors[:10]:  # Show first 10 errors
            logger.warning(f"  - {error}")

    logger.info("=" * 60)


# Create the DAG
with DAG(
    'etl_postgres_to_clickhouse',
    default_args=default_args,
    description='ETL pipeline: PostgreSQL databases -> ClickHouse data warehouse',
    schedule_interval='@daily',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['etl', 'postgres', 'clickhouse', 'warehouse'],
    doc_md=__doc__,
) as dag:

    # Start
    start = EmptyOperator(task_id='start')

    # Initialize ClickHouse
    init_ch = PythonOperator(
        task_id='init_clickhouse',
        python_callable=init_clickhouse,
    )

    # ETL tasks for each service (can run in parallel)
    etl_tasks = []
    for service_name in DB_CONFIGS.keys():
        task = PythonOperator(
            task_id=f'etl_{service_name}',
            python_callable=etl_service,
            op_kwargs={'service_name': service_name},
        )
        etl_tasks.append(task)

    # Summary
    summary = PythonOperator(
        task_id='generate_summary',
        python_callable=generate_summary,
        trigger_rule='all_done',  # Run even if some tasks fail
    )

    # End
    end = EmptyOperator(task_id='end')

    # Task dependencies
    # ETL tasks run in parallel after init
    start >> init_ch >> etl_tasks >> summary >> end
