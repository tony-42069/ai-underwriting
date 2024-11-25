from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import os
from dotenv import load_dotenv
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(verbose=True)

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db = None

    @classmethod
    async def connect_db(cls):
        try:
            MONGODB_URL = os.getenv("MONGODB_URL")
            logger.info(f"MongoDB URL found: {'Yes' if MONGODB_URL else 'No'}")
            
            if not MONGODB_URL:
                raise ValueError("MONGODB_URL environment variable is not set")
            
            logger.info("Connecting to MongoDB...")
            cls.client = AsyncIOMotorClient(
                MONGODB_URL,
                serverSelectionTimeoutMS=5000  # 5 second timeout
            )
            
            # Test the connection
            logger.info("Testing MongoDB connection...")
            await cls.client.admin.command('ping')
            logger.info("MongoDB ping successful!")
            
            cls.db = cls.client.ai_underwriting
            logger.info("MongoDB database selected: ai_underwriting")
            
            return cls.db
            
        except Exception as e:
            logger.error("MongoDB connection error:")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.error("Traceback:")
            logger.error(traceback.format_exc())
            raise

    @classmethod
    async def close_db(cls):
        try:
            if cls.client:
                logger.info("Closing MongoDB connection")
                cls.client.close()
                logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {str(e)}")
            raise