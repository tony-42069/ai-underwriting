"""
MongoDB configuration and client setup.
"""
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

logger = logging.getLogger(__name__)

class MongoDB:
    """MongoDB client and database management."""
    
    client: Optional[AsyncIOMotorClient] = None
    db = None
    
    @classmethod
    async def connect_db(cls, mongodb_url: str = "mongodb://localhost:27017", 
                        db_name: str = "ai_underwriting"):
        """
        Connect to MongoDB and initialize collections.
        
        Args:
            mongodb_url: MongoDB connection URL
            db_name: Database name
        """
        try:
            logger.info("Connecting to MongoDB...")
            cls.client = AsyncIOMotorClient(mongodb_url)
            cls.db = cls.client[db_name]
            
            # Ensure indexes
            await cls._create_indexes()
            
            logger.info("Successfully connected to MongoDB")
            return cls.db
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    @classmethod
    async def close_db(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("Closed MongoDB connection")
    
    @classmethod
    async def _create_indexes(cls):
        """Create necessary indexes for collections."""
        try:
            # Documents collection indexes
            await cls.db.documents.create_index("filename")
            await cls.db.documents.create_index("status")
            await cls.db.documents.create_index([
                ("processing_result.extractions.extractor", 1),
                ("processing_result.extractions.confidence.overall", -1)
            ])
            
            # Create TTL index for uploaded files (30 days)
            await cls.db.documents.create_index(
                "processing_result.processed_at",
                expireAfterSeconds=30 * 24 * 60 * 60
            )
            
            logger.info("Successfully created MongoDB indexes")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {str(e)}")
            raise
    
    @classmethod
    async def get_document_by_id(cls, document_id: str):
        """Get document by ID."""
        return await cls.db.documents.find_one({"_id": document_id})
    
    @classmethod
    async def get_documents_by_type(cls, extractor_type: str, min_confidence: float = 0.7):
        """Get documents by extraction type with minimum confidence."""
        cursor = cls.db.documents.find({
            "status": "completed",
            "processing_result.extractions": {
                "$elemMatch": {
                    "extractor": extractor_type,
                    "confidence.overall": {"$gte": min_confidence}
                }
            }
        })
        return await cursor.to_list(length=None)
    
    @classmethod
    async def get_recent_documents(cls, limit: int = 10):
        """Get most recently processed documents."""
        cursor = cls.db.documents.find(
            {"status": "completed"}
        ).sort(
            "processing_result.processed_at", -1
        ).limit(limit)
        return await cursor.to_list(length=None)
    
    @classmethod
    async def get_extraction_stats(cls):
        """Get statistics about document extractions."""
        pipeline = [
            {"$match": {"status": "completed"}},
            {"$unwind": "$processing_result.extractions"},
            {
                "$group": {
                    "_id": "$processing_result.extractions.extractor",
                    "count": {"$sum": 1},
                    "avg_confidence": {"$avg": "$processing_result.extractions.confidence.overall"},
                    "min_confidence": {"$min": "$processing_result.extractions.confidence.overall"},
                    "max_confidence": {"$max": "$processing_result.extractions.confidence.overall"}
                }
            }
        ]
        
        cursor = cls.db.documents.aggregate(pipeline)
        return await cursor.to_list(length=None)
    
    @classmethod
    async def cleanup_failed_documents(cls, max_age_hours: int = 24):
        """Clean up failed document processing records."""
        from datetime import datetime, timedelta
        
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        result = await cls.db.documents.delete_many({
            "status": "error",
            "processing_result.processed_at": {"$lt": cutoff.isoformat()}
        })
        
        logger.info(f"Cleaned up {result.deleted_count} failed documents")
