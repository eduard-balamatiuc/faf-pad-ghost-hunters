"""
MongoDB connector for ETL pipelines.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class MongoDBConnector:
    """Connector for MongoDB operations."""

    def __init__(self, config: Dict[str, str]):
        """
        Initialize MongoDB connector.

        Args:
            config: Dictionary with host, port, database, username, password
        """
        self.config = config
        self._client = None
        self._db = None

    def _get_client(self):
        """Get or create MongoDB client."""
        if self._client is None:
            from pymongo import MongoClient

            host = self.config['host']
            port = int(self.config['port'])
            username = self.config.get('username', '')
            password = self.config.get('password', '')
            database = self.config['database']

            if username and password:
                uri = f"mongodb://{username}:{password}@{host}:{port}/{database}?authSource=admin"
            else:
                uri = f"mongodb://{host}:{port}/{database}"

            self._client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self._db = self._client[database]

        return self._client, self._db

    def test_connection(self) -> bool:
        """Test MongoDB connection."""
        try:
            client, _ = self._get_client()
            client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB: {self.config['host']}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False

    def get_collections(self) -> List[str]:
        """Get list of collections in the database."""
        _, db = self._get_client()
        collections = db.list_collection_names()
        # Filter out system collections
        return [c for c in collections if not c.startswith('system.')]

    def get_collection_schema(self, collection_name: str, sample_size: int = 100) -> List[Tuple[str, str]]:
        """
        Infer schema from collection by sampling documents.

        Args:
            collection_name: Name of the collection
            sample_size: Number of documents to sample

        Returns:
            List of (field_name, inferred_type) tuples
        """
        _, db = self._get_client()
        collection = db[collection_name]

        # Sample documents to infer schema
        documents = list(collection.find().limit(sample_size))

        if not documents:
            return []

        # Collect all fields and their types
        field_types: Dict[str, set] = {}

        for doc in documents:
            for key, value in doc.items():
                if key not in field_types:
                    field_types[key] = set()
                field_types[key].add(self._infer_type(value))

        # Convert to schema format
        schema = []
        for field, types in field_types.items():
            # Use the most common/appropriate type
            if 'objectId' in types:
                inferred_type = 'objectId'
            elif 'date' in types:
                inferred_type = 'date'
            elif 'int' in types or 'long' in types:
                inferred_type = 'long'
            elif 'double' in types:
                inferred_type = 'double'
            elif 'bool' in types:
                inferred_type = 'bool'
            elif 'array' in types:
                inferred_type = 'array'
            elif 'object' in types:
                inferred_type = 'object'
            else:
                inferred_type = 'string'

            schema.append((field, inferred_type))

        return schema

    def _infer_type(self, value: Any) -> str:
        """Infer MongoDB type from Python value."""
        from bson import ObjectId

        if value is None:
            return 'null'
        elif isinstance(value, ObjectId):
            return 'objectId'
        elif isinstance(value, bool):
            return 'bool'
        elif isinstance(value, int):
            return 'long' if abs(value) > 2147483647 else 'int'
        elif isinstance(value, float):
            return 'double'
        elif isinstance(value, datetime):
            return 'date'
        elif isinstance(value, list):
            return 'array'
        elif isinstance(value, dict):
            return 'object'
        else:
            return 'string'

    def extract_data(
        self,
        collection_name: str,
        query: Optional[Dict] = None,
        projection: Optional[Dict] = None,
        limit: Optional[int] = None
    ) -> Tuple[List[str], List[Dict]]:
        """
        Extract data from a collection.

        Args:
            collection_name: Name of the collection
            query: MongoDB query filter
            projection: Fields to include/exclude
            limit: Maximum number of documents

        Returns:
            Tuple of (field_names, documents)
        """
        _, db = self._get_client()
        collection = db[collection_name]

        cursor = collection.find(query or {}, projection)
        if limit:
            cursor = cursor.limit(limit)

        documents = list(cursor)

        if not documents:
            return [], []

        # Get all unique field names across documents
        field_names = set()
        for doc in documents:
            field_names.update(doc.keys())

        field_names = sorted(list(field_names))

        # Convert ObjectId and datetime for serialization
        from bson import ObjectId

        processed_docs = []
        for doc in documents:
            processed = {}
            for field in field_names:
                value = doc.get(field)
                if isinstance(value, ObjectId):
                    processed[field] = str(value)
                elif isinstance(value, datetime):
                    processed[field] = value
                elif isinstance(value, (list, dict)):
                    processed[field] = value
                else:
                    processed[field] = value
            processed_docs.append(processed)

        return field_names, processed_docs

    def get_document_count(self, collection_name: str, query: Optional[Dict] = None) -> int:
        """Get count of documents in collection."""
        _, db = self._get_client()
        collection = db[collection_name]
        return collection.count_documents(query or {})

    def close(self):
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
