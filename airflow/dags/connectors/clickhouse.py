"""
ClickHouse database connector and utilities.
"""

import logging
from typing import List, Tuple, Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)


class ClickHouseConnector:
    """ClickHouse database connector for data warehouse operations."""

    def __init__(self, config: Dict[str, str]):
        """
        Initialize ClickHouse connector.

        Args:
            config: Dictionary with host, port, database, user, password
        """
        self.config = config
        self.base_url = f"http://{config['host']}:{config['port']}"
        self.session = requests.Session()

    def _get_params(self, include_database: bool = True) -> Dict[str, str]:
        """Get query parameters for ClickHouse requests."""
        params = {
            'user': self.config['user'],
            'password': self.config['password'],
        }
        if include_database:
            params['database'] = self.config['database']
        return params

    def execute_query(self, query: str, data: Optional[bytes] = None) -> str:
        """
        Execute a query on ClickHouse.

        Args:
            query: SQL query to execute
            data: Optional data payload (for INSERT operations)

        Returns:
            Response text from ClickHouse
        """
        params = self._get_params()

        if data:
            params['query'] = query
            response = self.session.post(self.base_url, params=params, data=data)
        else:
            response = self.session.post(self.base_url, params=params, data=query)

        if response.status_code != 200:
            raise Exception(f"ClickHouse error: {response.text}")

        return response.text

    def ensure_database(self) -> None:
        """Ensure the target database exists."""
        params = self._get_params(include_database=False)
        query = f"CREATE DATABASE IF NOT EXISTS {self.config['database']}"

        response = self.session.post(self.base_url, params=params, data=query)

        if response.status_code != 200:
            raise Exception(f"Failed to create database: {response.text}")

        logger.info(f"Database {self.config['database']} is ready")

    def create_table(
        self,
        table_name: str,
        columns: List[Tuple[str, str]],
        order_by: Optional[List[str]] = None,
        engine: str = 'ReplacingMergeTree'
    ) -> None:
        """
        Create a table in ClickHouse.

        Args:
            table_name: Name of the table
            columns: List of (column_name, column_type) tuples
            order_by: Columns for ORDER BY clause
            engine: Table engine (default: ReplacingMergeTree)
        """
        columns_with_meta = columns + [
            ('_etl_loaded_at', 'DateTime DEFAULT now()'),
            ('_etl_source', f"String DEFAULT '{table_name.split('_')[0]}'"),
        ]

        columns_str = ",\n    ".join(f"`{name}` {dtype}" for name, dtype in columns_with_meta)

        if order_by:
            order_str = ', '.join(f'`{col}`' for col in order_by)
        else:
            order_str = 'tuple()'

        if engine == 'ReplacingMergeTree':
            engine_str = f"ReplacingMergeTree(_etl_loaded_at)"
        else:
            engine_str = engine

        query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {columns_str}
        ) ENGINE = {engine_str}
        ORDER BY ({order_str})
        """

        self.execute_query(query)
        logger.info(f"Created/verified table: {table_name}")

    def truncate_table(self, table_name: str) -> None:
        """
        Truncate a table (remove all data).

        Args:
            table_name: Name of the table
        """
        try:
            self.execute_query(f"TRUNCATE TABLE IF EXISTS {table_name}")
            logger.info(f"Truncated table: {table_name}")
        except Exception as e:
            logger.warning(f"Could not truncate {table_name}: {e}")

    def insert_data(
        self,
        table_name: str,
        columns: List[str],
        data: bytes,
        format: str = 'CSV'
    ) -> None:
        """
        Insert data into a table.

        Args:
            table_name: Name of the table
            columns: List of column names
            data: Data payload in the specified format
            format: Data format (CSV, JSONEachRow, etc.)
        """
        cols_str = ', '.join(f'`{c}`' for c in columns)
        query = f"INSERT INTO {table_name} ({cols_str}) FORMAT {format}"

        self.execute_query(query, data)
        logger.info(f"Inserted data into {table_name}")

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists.

        Args:
            table_name: Name of the table

        Returns:
            True if table exists, False otherwise
        """
        query = f"EXISTS TABLE {table_name}"
        result = self.execute_query(query)
        return result.strip() == '1'

    def get_row_count(self, table_name: str) -> int:
        """
        Get row count for a table.

        Args:
            table_name: Name of the table

        Returns:
            Number of rows
        """
        query = f"SELECT COUNT(*) FROM {table_name}"
        result = self.execute_query(query)
        return int(result.strip())

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/ping")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_tables(self) -> List[str]:
        """
        Get list of tables in the database.

        Returns:
            List of table names
        """
        query = "SHOW TABLES"
        result = self.execute_query(query)
        return [line.strip() for line in result.strip().split('\n') if line.strip()]
