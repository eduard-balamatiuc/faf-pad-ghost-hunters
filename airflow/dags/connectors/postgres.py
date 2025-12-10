"""
PostgreSQL database connector and utilities.
"""

import logging
from typing import List, Tuple, Any, Dict, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class PostgresConnector:
    """PostgreSQL database connector for data extraction."""

    def __init__(self, config: Dict[str, str]):
        """
        Initialize PostgreSQL connector.

        Args:
            config: Dictionary with host, port, database, user, password
        """
        self.config = config

    @contextmanager
    def get_connection(self):
        """Context manager for PostgreSQL connections."""
        import psycopg2

        conn = psycopg2.connect(
            host=self.config['host'],
            port=self.config['port'],
            database=self.config['database'],
            user=self.config['user'],
            password=self.config['password']
        )
        try:
            yield conn
        finally:
            conn.close()

    def get_tables(self, schema: str = 'public') -> List[str]:
        """
        Get list of tables in the database.

        Args:
            schema: Database schema to query (default: public)

        Returns:
            List of table names
        """
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            AND table_type = 'BASE TABLE'
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (schema,))
            tables = [row[0] for row in cursor.fetchall()]
            cursor.close()

        return tables

    def get_table_schema(self, table_name: str, schema: str = 'public') -> List[Tuple[str, str, str]]:
        """
        Get table schema (columns with types).

        Args:
            table_name: Name of the table
            schema: Database schema (default: public)

        Returns:
            List of tuples (column_name, data_type, is_nullable)
        """
        query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (schema, table_name))
            columns = cursor.fetchall()
            cursor.close()

        return columns

    def get_primary_keys(self, table_name: str, schema: str = 'public') -> List[str]:
        """
        Get primary key columns for a table.

        Args:
            table_name: Name of the table
            schema: Database schema (default: public)

        Returns:
            List of primary key column names
        """
        query = """
            SELECT a.attname
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            JOIN pg_class c ON c.oid = i.indrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE i.indisprimary
            AND c.relname = %s
            AND n.nspname = %s
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (table_name, schema))
            pk_columns = [row[0] for row in cursor.fetchall()]
            cursor.close()

        return pk_columns

    def extract_data(self, table_name: str, columns: Optional[List[str]] = None) -> Tuple[List[str], List[Tuple]]:
        """
        Extract data from a table.

        Args:
            table_name: Name of the table
            columns: Optional list of columns to extract (default: all)

        Returns:
            Tuple of (column_names, rows)
        """
        if columns:
            cols_str = ', '.join(f'"{c}"' for c in columns)
        else:
            cols_str = '*'

        query = f'SELECT {cols_str} FROM "{table_name}"'

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]
            cursor.close()

        logger.info(f"Extracted {len(rows)} rows from {table_name}")
        return col_names, rows

    def get_row_count(self, table_name: str) -> int:
        """
        Get row count for a table.

        Args:
            table_name: Name of the table

        Returns:
            Number of rows
        """
        query = f'SELECT COUNT(*) FROM "{table_name}"'

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            count = cursor.fetchone()[0]
            cursor.close()

        return count

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
