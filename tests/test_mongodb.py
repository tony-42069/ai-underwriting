import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from bson import ObjectId

from backend.db.mongodb import MongoDB


class TestMongoDB:
    """Tests for MongoDB class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock MongoDB client."""
        mock_db = MagicMock()
        mock_client = MagicMock()
        mock_client.__getitem__ = MagicMock(return_value=mock_db)
        mock_db.__getitem__ = MagicMock(return_value=MagicMock())
        return mock_client, mock_db

    @pytest.mark.asyncio
    async def test_connect_db_success(self, mock_client):
        """Test successful database connection."""
        mock_client_instance, mock_db = mock_client

        with patch.object(MongoDB, 'client', None):
            with patch.object(MongoDB, 'db', None):
                with patch('motor.motor_asyncio.AsyncIOMotorClient', return_value=mock_client_instance):
                    result = await MongoDB.connect_db(
                        mongodb_url="mongodb://localhost:27017",
                        db_name="test_db"
                    )

        assert MongoDB.client is not None
        assert MongoDB.db is not None

    @pytest.mark.asyncio
    async def test_close_db(self, mock_client):
        """Test closing database connection."""
        mock_client_instance, mock_db = mock_client

        MongoDB.client = mock_client_instance
        MongoDB.db = mock_db

        await MongoDB.close_db()

        mock_client_instance.close.assert_called_once()
        assert MongoDB.client is None
        assert MongoDB.db is None

    @pytest.mark.asyncio
    async def test_create_indexes(self, mock_client):
        """Test index creation."""
        mock_client_instance, mock_db = mock_client

        MongoDB.client = mock_client_instance
        MongoDB.db = mock_db

        with patch.object(mock_db.documents, 'create_index', new_callable=AsyncMock) as mock_create_index:
            await MongoDB._create_indexes()

            assert mock_db.documents.create_index.called

    @pytest.mark.asyncio
    async def test_get_document_by_id(self, mock_client):
        """Test getting document by ID."""
        mock_client_instance, mock_db = mock_client

        test_doc = {"_id": ObjectId(), "filename": "test.pdf"}
        mock_db.documents.find_one = AsyncMock(return_value=test_doc)

        MongoDB.client = mock_client_instance
        MongoDB.db = mock_db

        result = await MongoDB.get_document_by_id(str(test_doc["_id"]))

        assert result == test_doc
        mock_db.documents.find_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document_by_id_not_found(self, mock_client):
        """Test getting non-existent document."""
        mock_client_instance, mock_db = mock_client

        mock_db.documents.find_one = AsyncMock(return_value=None)

        MongoDB.client = mock_client_instance
        MongoDB.db = mock_db

        result = await MongoDB.get_document_by_id(str(ObjectId()))

        assert result is None

    @pytest.mark.asyncio
    async def test_get_documents_by_type(self, mock_client):
        """Test getting documents by extraction type."""
        mock_client_instance, mock_db = mock_client

        test_docs = [
            {"_id": ObjectId(), "filename": "doc1.pdf"},
            {"_id": ObjectId(), "filename": "doc2.pdf"},
        ]

        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=test_docs)
        mock_db.documents.find = MagicMock(return_value=mock_cursor)

        MongoDB.client = mock_client_instance
        MongoDB.db = mock_db

        result = await MongoDB.get_documents_by_type("RentRollExtractor", min_confidence=0.7)

        assert len(result) == 2
        mock_db.documents.find.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recent_documents(self, mock_client):
        """Test getting recent documents."""
        mock_client_instance, mock_db = mock_client

        test_docs = [
            {"_id": ObjectId(), "filename": "doc1.pdf"},
            {"_id": ObjectId(), "filename": "doc2.pdf"},
        ]

        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=test_docs)
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_db.documents.find = MagicMock(return_value=mock_cursor)

        MongoDB.client = mock_client_instance
        MongoDB.db = mock_db

        result = await MongoDB.get_recent_documents(limit=10)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_extraction_stats(self, mock_client):
        """Test getting extraction statistics."""
        mock_client_instance, mock_db = mock_client

        test_stats = [
            {"_id": "RentRollExtractor", "count": 10, "avg_confidence": 0.9},
            {"_id": "PLStatementExtractor", "count": 5, "avg_confidence": 0.85},
        ]

        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=test_stats)
        mock_db.documents.aggregate = MagicMock(return_value=mock_cursor)

        MongoDB.client = mock_client_instance
        MongoDB.db = mock_db

        result = await MongoDB.get_extraction_stats()

        assert len(result) == 2
        assert result[0]["_id"] == "RentRollExtractor"

    @pytest.mark.asyncio
    async def test_cleanup_failed_documents(self, mock_client):
        """Test cleanup of failed documents."""
        mock_client_instance, mock_db = mock_client

        mock_db.documents.delete_many = AsyncMock(return_value=MagicMock(deleted_count=5))

        MongoDB.client = mock_client_instance
        MongoDB.db = mock_db

        result = await MongoDB.cleanup_failed_documents(max_age_hours=24)

        assert result == 5
        mock_db.documents.delete_many.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_db_failure(self, mock_client):
        """Test handling of connection failure."""
        mock_client_instance, mock_db = mock_client

        with patch.object(MongoDB, 'client', None):
            with patch.object(MongoDB, 'db', None):
                with patch('motor.motor_asyncio.AsyncIOMotorClient', side_effect=Exception("Connection failed")):
                    with pytest.raises(Exception):
                        await MongoDB.connect_db()

    def test_class_attributes(self):
        """Test class-level attributes are initialized correctly."""
        assert MongoDB.client is None
        assert MongoDB.db is None

    @pytest.mark.asyncio
    async def test_ttl_index_creation(self, mock_client):
        """Test that TTL index is created with correct expiration."""
        mock_client_instance, mock_db = mock_client

        MongoDB.client = mock_client_instance
        MongoDB.db = mock_db

        with patch.object(mock_db.documents, 'create_index', new_callable=AsyncMock) as mock_create_index:
            await MongoDB._create_indexes()

            calls = mock_db.documents.create_index.call_args_list
            ttl_call = [c for c in calls if "expireAfterSeconds" in str(c)]
            assert len(ttl_call) > 0
