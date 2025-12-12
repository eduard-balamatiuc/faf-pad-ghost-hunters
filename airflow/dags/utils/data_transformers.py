"""
Data transformation utilities for ETL pipelines.
"""

import csv
import io
import json
from datetime import datetime, date, time
from decimal import Decimal
from typing import List, Tuple, Any
from uuid import UUID


def format_datetime_for_clickhouse(val: datetime) -> str:
    """
    Format datetime for ClickHouse DateTime type.
    ClickHouse DateTime expects: YYYY-MM-DD hh:mm:ss (no microseconds, no timezone)
    """
    return val.strftime('%Y-%m-%d %H:%M:%S')


def format_date_for_clickhouse(val: date) -> str:
    """
    Format date for ClickHouse Date type.
    """
    return val.strftime('%Y-%m-%d')


def format_time_for_clickhouse(val: time) -> str:
    """
    Format time for ClickHouse String type.
    """
    return val.strftime('%H:%M:%S')


def transform_row_for_clickhouse(row: Tuple[Any, ...]) -> List[str]:
    """
    Transform a database row for ClickHouse CSV import.

    Args:
        row: Tuple of values from source database

    Returns:
        List of string values ready for CSV export
    """
    converted = []

    for val in row:
        if val is None:
            converted.append('\\N')
        elif isinstance(val, bool):
            converted.append('1' if val else '0')
        elif isinstance(val, datetime):
            # Handle datetime with microseconds and timezone
            converted.append(format_datetime_for_clickhouse(val))
        elif isinstance(val, date):
            converted.append(format_date_for_clickhouse(val))
        elif isinstance(val, time):
            converted.append(format_time_for_clickhouse(val))
        elif isinstance(val, UUID):
            converted.append(str(val))
        elif isinstance(val, Decimal):
            converted.append(str(val))
        elif isinstance(val, (dict, list)):
            converted.append(json.dumps(val))
        elif isinstance(val, bytes):
            converted.append(val.hex())
        else:
            converted.append(str(val))

    return converted


def rows_to_csv(rows: List[Tuple[Any, ...]]) -> bytes:
    """
    Convert rows to CSV format for ClickHouse import.

    Args:
        rows: List of row tuples

    Returns:
        CSV data as bytes
    """
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    for row in rows:
        converted_row = transform_row_for_clickhouse(row)
        writer.writerow(converted_row)

    csv_data = output.getvalue()
    output.close()

    return csv_data.encode('utf-8')


def json_to_clickhouse_row(doc: dict, fields: List[str]) -> List[str]:
    """
    Convert a JSON document (e.g., from MongoDB) to ClickHouse row.

    Args:
        doc: JSON document
        fields: List of field names to extract

    Returns:
        List of string values
    """
    converted = []

    for field in fields:
        val = doc.get(field)

        if val is None:
            converted.append('\\N')
        elif isinstance(val, bool):
            converted.append('1' if val else '0')
        elif isinstance(val, datetime):
            converted.append(format_datetime_for_clickhouse(val))
        elif isinstance(val, date):
            converted.append(format_date_for_clickhouse(val))
        elif isinstance(val, (dict, list)):
            converted.append(json.dumps(val))
        else:
            converted.append(str(val))

    return converted


def sanitize_column_name(name: str) -> str:
    """
    Sanitize column name for ClickHouse compatibility.

    Args:
        name: Original column name

    Returns:
        Sanitized column name
    """
    # Replace spaces and special chars with underscores
    sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in name)

    # Ensure it doesn't start with a number
    if sanitized and sanitized[0].isdigit():
        sanitized = f"col_{sanitized}"

    return sanitized.lower()
