import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class CleanupConfig:
    """Configuration for file cleanup operations."""

    def __init__(
        self,
        uploads_dir: str = "backend/uploads",
        completed_retention_days: int = 30,
        failed_retention_hours: int = 24,
        pending_retention_hours: int = 4,
        max_temp_file_age_hours: int = 2,
        cleanup_batch_size: int = 100,
    ):
        self.uploads_dir = Path(uploads_dir)
        self.completed_retention_days = completed_retention_days
        self.failed_retention_hours = failed_retention_hours
        self.pending_retention_hours = pending_retention_hours
        self.max_temp_file_age_hours = max_temp_file_age_hours
        self.cleanup_batch_size = cleanup_batch_size


class FileCleanupService:
    """Service for cleaning up temporary and expired files."""

    def __init__(self, config: CleanupConfig = None):
        """Initialize cleanup service with configuration."""
        self.config = config or CleanupConfig()
        self._cleanup_lock = False

    async def cleanup_expired_documents(
        self, db
    ) -> Dict[str, int]:
        """Clean up expired document records and their files."""
        results = {"deleted_records": 0, "deleted_files": 0, "errors": 0}

        now = datetime.now()

        completed_cutoff = now - timedelta(days=self.config.completed_retention_days)
        failed_cutoff = now - timedelta(hours=self.config.failed_retention_hours)
        pending_cutoff = now - timedelta(hours=self.config.pending_retention_hours)

        try:
            completed_query = {
                "status": "completed",
                "created_at": {"$lt": completed_cutoff.isoformat()}
            }
            completed_docs = await db.documents.find(completed_query).to_list(
                length=self.config.cleanup_batch_size
            )

            for doc in completed_docs:
                try:
                    file_path = doc.get("path")
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                        results["deleted_files"] += 1

                    await db.documents.delete_one({"_id": doc["_id"]})
                    results["deleted_records"] += 1
                except Exception as e:
                    logger.error(f"Error deleting completed document {doc['_id']}: {e}")
                    results["errors"] += 1

            failed_query = {
                "status": "error",
                "created_at": {"$lt": failed_cutoff.isoformat()}
            }
            failed_docs = await db.documents.find(failed_query).to_list(
                length=self.config.cleanup_batch_size
            )

            for doc in failed_docs:
                try:
                    file_path = doc.get("path")
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                        results["deleted_files"] += 1

                    await db.documents.delete_one({"_id": doc["_id"]})
                    results["deleted_records"] += 1
                except Exception as e:
                    logger.error(f"Error deleting failed document {doc['_id']}: {e}")
                    results["errors"] += 1

            pending_query = {
                "status": "pending",
                "created_at": {"$lt": pending_cutoff.isoformat()}
            }
            pending_docs = await db.documents.find(pending_query).to_list(
                length=self.config.cleanup_batch_size
            )

            for doc in pending_docs:
                try:
                    file_path = doc.get("path")
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                        results["deleted_files"] += 1

                    await db.documents.delete_one({"_id": doc["_id"]})
                    results["deleted_records"] += 1
                except Exception as e:
                    logger.error(f"Error deleting pending document {doc['_id']}: {e}")
                    results["errors"] += 1

            logger.info(
                f"Cleanup completed: {results['deleted_records']} records, "
                f"{results['deleted_files']} files, {results['errors']} errors"
            )

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            results["errors"] += 1

        return results

    async def cleanup_temp_files(self) -> Dict[str, int]:
        """Clean up temporary files in uploads directory."""
        results = {"scanned": 0, "deleted": 0, "errors": 0}

        if not self.config.uploads_dir.exists():
            return results

        max_age = datetime.now() - timedelta(hours=self.config.max_temp_file_age_hours)

        try:
            for file_path in self.config.uploads_dir.iterdir():
                results["scanned"] += 1

                if file_path.is_file():
                    file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

                    if file_mtime < max_age:
                        try:
                            file_path.unlink()
                            results["deleted"] += 1
                            logger.debug(f"Deleted temp file: {file_path}")
                        except Exception as e:
                            logger.error(f"Error deleting {file_path}: {e}")
                            results["errors"] += 1

        except Exception as e:
            logger.error(f"Error scanning temp files: {e}")
            results["errors"] += 1

        logger.info(f"Temp cleanup: {results['deleted']} files deleted")
        return results

    async def cleanup_orphaned_files(self, db) -> Dict[str, int]:
        """Clean up files without corresponding database records."""
        results = {"scanned": 0, "deleted": 0, "errors": 0}

        if not self.config.uploads_dir.exists():
            return results

        try:
            document_paths = set()
            async for doc in db.documents.find({}, {"path": 1}):
                if doc.get("path"):
                    document_paths.add(doc["path"])

            for file_path in self.config.uploads_dir.iterdir():
                if file_path.is_file():
                    results["scanned"] += 1

                    if str(file_path) not in document_paths:
                        try:
                            file_path.unlink()
                            results["deleted"] += 1
                            logger.info(f"Deleted orphaned file: {file_path}")
                        except Exception as e:
                            logger.error(f"Error deleting {file_path}: {e}")
                            results["errors"] += 1

        except Exception as e:
            logger.error(f"Error scanning for orphaned files: {e}")
            results["errors"] += 1

        logger.info(f"Orphaned cleanup: {results['deleted']} files deleted")
        return results

    async def run_full_cleanup(self, db) -> Dict[str, int]:
        """Run all cleanup operations."""
        results = {
            "expired_documents": {},
            "temp_files": {},
            "orphaned_files": {},
        }

        if self._cleanup_lock:
            logger.warning("Cleanup already in progress")
            return results

        self._cleanup_lock = True

        try:
            results["expired_documents"] = await self.cleanup_expired_documents(db)
            results["temp_files"] = await self.cleanup_temp_files()
            results["orphaned_files"] = await self.cleanup_orphaned_files(db)

            total_deleted = (
                results["expired_documents"].get("deleted_records", 0)
                + results["temp_files"].get("deleted", 0)
                + results["orphaned_files"].get("deleted", 0)
            )

            logger.info(f"Full cleanup completed: {total_deleted} items deleted")

        finally:
            self._cleanup_lock = False

        return results

    def get_storage_stats(self, db) -> Dict:
        """Get storage statistics."""
        stats = {
            "uploads_directory": {},
            "database_counts": {},
            "oldest_document": None,
        }

        if self.config.uploads_dir.exists():
            total_size = 0
            file_count = 0
            for file_path in self.config.uploads_dir.iterdir():
                if file_path.is_file():
                    file_count += 1
                    total_size += file_path.stat().st_size

            stats["uploads_directory"] = {
                "path": str(self.config.uploads_dir),
                "file_count": file_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
            }

        try:
            stats["database_counts"] = {
                "total": await db.documents.count_documents({}),
                "completed": await db.documents.count_documents({"status": "completed"}),
                "pending": await db.documents.count_documents({"status": "pending"}),
                "error": await db.documents.count_documents({"status": "error"}),
            }

            oldest = await db.documents.find_one(
                {},
                sort=[("created_at", 1)]
            )
            if oldest:
                stats["oldest_document"] = {
                    "id": str(oldest["_id"]),
                    "created_at": oldest.get("created_at"),
                    "status": oldest.get("status"),
                }

        except Exception as e:
            logger.error(f"Error getting database stats: {e}")

        return stats


class ScheduledCleanup:
    """Scheduled cleanup task manager."""

    def __init__(self, cleanup_service: FileCleanupService):
        self.cleanup_service = cleanup_service
        self._task: Optional[asyncio.Task] = None
        self._interval_hours: int = 24

    def start(self, interval_hours: int = 24):
        """Start scheduled cleanup."""
        self._interval_hours = interval_hours

        async def run_periodic():
            while True:
                try:
                    from db.mongodb import MongoDB
                    await self.cleanup_service.run_full_cleanup(MongoDB.db)
                except Exception as e:
                    logger.error(f"Scheduled cleanup error: {e}")

                await asyncio.sleep(self._interval_hours * 3600)

        self._task = asyncio.create_task(run_periodic())
        logger.info(f"Scheduled cleanup started (every {interval_hours} hours)")

    def stop(self):
        """Stop scheduled cleanup."""
        if self._task:
            self._task.cancel()
            self._task = None
            logger.info("Scheduled cleanup stopped")

    async def run_once(self, db) -> Dict:
        """Run cleanup once."""
        return await self.cleanup_service.run_full_cleanup(db)
