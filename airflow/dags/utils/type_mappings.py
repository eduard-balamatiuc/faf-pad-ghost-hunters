"""
Type mappings between different database systems.
"""

# PostgreSQL to ClickHouse type mapping
PG_TO_CH_TYPES = {
    # Integers
    'integer': 'Int32',
    'bigint': 'Int64',
    'smallint': 'Int16',
    'serial': 'Int32',
    'bigserial': 'Int64',

    # Booleans
    'boolean': 'UInt8',

    # Floating point
    'real': 'Float32',
    'double precision': 'Float64',
    'numeric': 'Decimal(18, 4)',
    'decimal': 'Decimal(18, 4)',

    # Strings
    'character varying': 'String',
    'varchar': 'String',
    'character': 'String',
    'char': 'String',
    'text': 'String',

    # UUID
    'uuid': 'UUID',

    # JSON
    'json': 'String',
    'jsonb': 'String',

    # Date/Time
    'timestamp without time zone': 'DateTime',
    'timestamp with time zone': 'DateTime',
    'timestamp': 'DateTime',
    'date': 'Date',
    'time without time zone': 'String',
    'time with time zone': 'String',
    'interval': 'String',

    # Binary
    'bytea': 'String',

    # Network
    'inet': 'String',
    'cidr': 'String',
    'macaddr': 'String',

    # Arrays (stored as JSON strings)
    'array': 'String',
    'ARRAY': 'String',
}


def map_pg_type_to_ch(pg_type: str, is_nullable: bool = False) -> str:
    """
    Map PostgreSQL data type to ClickHouse data type.

    Args:
        pg_type: PostgreSQL data type
        is_nullable: Whether the column is nullable

    Returns:
        ClickHouse data type string
    """
    pg_type_lower = pg_type.lower()

    # Find matching type
    ch_type = 'String'  # Default fallback
    for pg_pattern, mapped_type in PG_TO_CH_TYPES.items():
        if pg_pattern in pg_type_lower:
            ch_type = mapped_type
            break

    # Wrap in Nullable if needed (except for String which handles nulls well)
    if is_nullable and ch_type not in ['String', 'UUID']:
        ch_type = f"Nullable({ch_type})"

    return ch_type


# MongoDB to ClickHouse type mapping (for future use)
MONGO_TO_CH_TYPES = {
    'string': 'String',
    'int': 'Int32',
    'long': 'Int64',
    'double': 'Float64',
    'bool': 'UInt8',
    'date': 'DateTime',
    'objectId': 'String',
    'array': 'String',
    'object': 'String',
}


def map_mongo_type_to_ch(mongo_type: str, is_nullable: bool = False) -> str:
    """
    Map MongoDB data type to ClickHouse data type.

    Args:
        mongo_type: MongoDB data type
        is_nullable: Whether the field is nullable

    Returns:
        ClickHouse data type string
    """
    ch_type = MONGO_TO_CH_TYPES.get(mongo_type.lower(), 'String')

    if is_nullable and ch_type not in ['String']:
        ch_type = f"Nullable({ch_type})"

    return ch_type
