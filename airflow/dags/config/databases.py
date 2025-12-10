"""
Database configurations for ETL pipelines.
All connection details are loaded from environment variables.
"""

import os

# PostgreSQL Service Databases
DB_CONFIGS = {
    'user_mgmt': {
        'host': os.getenv('USER_MGMT_DB_HOST', 'user-mgmt-postgres'),
        'port': os.getenv('USER_MGMT_DB_PORT', '5432'),
        'database': os.getenv('USER_MGMT_DB_DBNAME', 'user_management'),
        'user': os.getenv('USER_MGMT_DB_USER', 'postgres'),
        'password': os.getenv('USER_MGMT_DB_PASSWORD', ''),
    },
    'inventory': {
        'host': os.getenv('INVENTORY_SVC_DB_HOST', 'inventory-postgres'),
        'port': os.getenv('INVENTORY_SVC_DB_PORT', '5432'),
        'database': os.getenv('INVENTORY_SVC_DB_DATABASE', 'inventory_db'),
        'user': os.getenv('INVENTORY_SVC_DB_USERNAME', 'postgres'),
        'password': os.getenv('INVENTORY_SVC_DB_PASSWORD', ''),
    },
    'ghost': {
        'host': os.getenv('GHOST_SVC_DB_HOST', 'ghost-postgres'),
        'port': os.getenv('GHOST_SVC_DB_PORT', '5436'),
        'database': os.getenv('GHOST_SVC_DB_NAME', 'ghost_db'),
        'user': os.getenv('GHOST_SVC_DB_USER', 'ghost_user'),
        'password': os.getenv('GHOST_SVC_DB_PASSWORD', ''),
    },
    'shop': {
        'host': os.getenv('SHOP_SERVICE_DB_HOST', 'shop-postgres'),
        'port': os.getenv('SHOP_SERVICE_DB_PORT', '5434'),
        'database': os.getenv('SHOP_SERVICE_DB_NAME', 'shop_db'),
        'user': os.getenv('SHOP_SERVICE_DB_USER', 'postgres'),
        'password': os.getenv('SHOP_SERVICE_DB_PASSWORD', ''),
    },
}

# ClickHouse Data Warehouse
CLICKHOUSE_CONFIG = {
    'host': os.getenv('CLICKHOUSE_HOST', 'clickhouse'),
    'port': os.getenv('CLICKHOUSE_HTTP_PORT', '8123'),
    'database': os.getenv('CLICKHOUSE_DB', 'warehouse'),
    'user': os.getenv('CLICKHOUSE_USER', 'default'),
    'password': os.getenv('CLICKHOUSE_PASSWORD', ''),
}

# Redis Service Databases (for future use)
REDIS_CONFIGS = {
    'gateway': {
        'host': os.getenv('GATEWAY_REDIS_HOST', 'gateway-redis'),
        'port': os.getenv('GATEWAY_REDIS_PORT', '6370'),
    },
    'location': {
        'host': os.getenv('LOCATION_SVC_REDIS_HOST', 'location-redis'),
        'port': os.getenv('LOCATION_SVC_REDIS_PORT', '6377'),
    },
    'map': {
        'host': os.getenv('MAP_SERVICE_REDIS_HOST', 'map-redis'),
        'port': os.getenv('MAP_SERVICE_REDIS_PORT', '6375'),
    },
    'lobby': {
        'host': os.getenv('LOBBY_SERVICE_REDIS_HOST', 'lobby-redis'),
        'port': os.getenv('LOBBY_SERVICE_REDIS_PORT', '6374'),
    },
    'journal': {
        'host': os.getenv('JOURNAL_SERVICE_REDIS_HOST', 'journal-redis'),
        'port': os.getenv('JOURNAL_SERVICE_REDIS_PORT', '6379'),
        'password': os.getenv('JOURNAL_SERVICE_REDIS_PASSWORD', ''),
    },
    'ghost_ai': {
        'host': os.getenv('GHOST_AI_SVC_REDIS_HOST', 'ghost-ai-redis'),
        'port': os.getenv('GHOST_AI_SVC_REDIS_PORT', '6372'),
    },
    'discovery': {
        'host': os.getenv('DISCOVERY_REDIS_HOST', 'discovery-redis'),
        'port': os.getenv('DISCOVERY_REDIS_PORT', '6379'),
    },
}

# MongoDB Service Databases
MONGO_CONFIGS = {
    'chat': {
        'host': os.getenv('CHAT_SVC_MONGO_HOST', 'chat-mongo'),
        'port': os.getenv('CHAT_SVC_MONGO_PORT', '27017'),
        'database': os.getenv('CHAT_SVC_MONGO_DATABASE', 'chat-mongo'),
        'username': os.getenv('CHAT_SVC_MONGO_USERNAME', 'admin'),
        'password': os.getenv('CHAT_SVC_MONGO_PASSWORD', ''),
    },
}
