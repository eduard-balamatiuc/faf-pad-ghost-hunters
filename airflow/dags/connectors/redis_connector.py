"""
Redis connector for ETL pipelines.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class RedisConnector:
    """Connector for Redis operations."""

    def __init__(self, config: Dict[str, str]):
        """
        Initialize Redis connector.

        Args:
            config: Dictionary with host, port, db (optional), password (optional)
        """
        self.config = config
        self._client = None

    def _get_client(self):
        """Get or create Redis client."""
        if self._client is None:
            import redis

            host = self.config['host']
            port = int(self.config['port'])
            db = int(self.config.get('db', 0))
            password = self.config.get('password')

            self._client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_timeout=5
            )

        return self._client

    def test_connection(self) -> bool:
        """Test Redis connection."""
        try:
            client = self._get_client()
            client.ping()
            logger.info(f"Successfully connected to Redis: {self.config['host']}:{self.config['port']}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False

    def get_all_keys(self, pattern: str = '*') -> List[str]:
        """Get all keys matching pattern."""
        client = self._get_client()
        keys = []
        cursor = 0

        while True:
            cursor, batch = client.scan(cursor, match=pattern, count=1000)
            keys.extend(batch)
            if cursor == 0:
                break

        return keys

    def get_key_type(self, key: str) -> str:
        """Get the type of a Redis key."""
        client = self._get_client()
        return client.type(key)

    def get_key_value(self, key: str) -> Tuple[str, Any]:
        """
        Get value of a key based on its type.

        Returns:
            Tuple of (type, value)
        """
        client = self._get_client()
        key_type = self.get_key_type(key)

        try:
            if key_type == 'string':
                value = client.get(key)
            elif key_type == 'hash':
                value = client.hgetall(key)
            elif key_type == 'list':
                value = client.lrange(key, 0, -1)
            elif key_type == 'set':
                value = list(client.smembers(key))
            elif key_type == 'zset':
                value = client.zrange(key, 0, -1, withscores=True)
            elif key_type == 'none':
                value = None
            else:
                value = None
                logger.warning(f"Unknown key type: {key_type} for key: {key}")

            return key_type, value
        except Exception as e:
            logger.error(f"Error getting value for key {key}: {e}")
            return key_type, None

    def get_key_ttl(self, key: str) -> int:
        """Get TTL for a key. Returns -1 if no expiry, -2 if key doesn't exist."""
        client = self._get_client()
        return client.ttl(key)

    def get_db_size(self) -> int:
        """Get number of keys in the database."""
        client = self._get_client()
        return client.dbsize()

    def get_info(self) -> Dict[str, Any]:
        """Get Redis server info."""
        client = self._get_client()
        return client.info()

    def extract_all_data(self, pattern: str = '*') -> List[Dict[str, Any]]:
        """
        Extract all data from Redis as a list of records.

        Each record contains:
        - key: The Redis key
        - type: The data type (string, hash, list, set, zset)
        - value: The value (serialized as JSON string for complex types)
        - ttl: Time to live (-1 if no expiry)

        Returns:
            List of dictionaries representing Redis data
        """
        keys = self.get_all_keys(pattern)
        records = []

        for key in keys:
            try:
                key_type, value = self.get_key_value(key)
                ttl = self.get_key_ttl(key)

                # Serialize complex values to JSON string
                if isinstance(value, (dict, list, tuple)):
                    value_str = json.dumps(value, default=str)
                elif value is None:
                    value_str = None
                else:
                    value_str = str(value)

                records.append({
                    'key': key,
                    'type': key_type,
                    'value': value_str,
                    'ttl': ttl if ttl >= 0 else None,
                })
            except Exception as e:
                logger.error(f"Error extracting key {key}: {e}")

        return records

    def extract_keys_by_prefix(self, prefix: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract keys grouped by prefix pattern.

        Args:
            prefix: Key prefix to group by (e.g., "user:", "session:")

        Returns:
            Dictionary mapping prefixes to their records
        """
        keys = self.get_all_keys(f"{prefix}*")
        records = []

        for key in keys:
            try:
                key_type, value = self.get_key_value(key)
                ttl = self.get_key_ttl(key)

                if isinstance(value, (dict, list, tuple)):
                    value_str = json.dumps(value, default=str)
                elif value is None:
                    value_str = None
                else:
                    value_str = str(value)

                records.append({
                    'key': key,
                    'type': key_type,
                    'value': value_str,
                    'ttl': ttl if ttl >= 0 else None,
                })
            except Exception as e:
                logger.error(f"Error extracting key {key}: {e}")

        return records

    def close(self):
        """Close Redis connection."""
        if self._client:
            self._client.close()
            self._client = None
