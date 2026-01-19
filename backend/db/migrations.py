"""
Database migration service for MongoDB.

This module provides migration capabilities for MongoDB collections
including index creation, schema updates, and data migrations.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.database import Database
from pymongo.collection import Collection

logger = logging.getLogger(__name__)


class Migration:
    """Base class for database migrations."""

    version: str
    description: str

    def up(self, db: Database) -> None:
        """Apply migration."""
        raise NotImplementedError

    def down(self, db: Database) -> None:
        """Rollback migration."""
        raise NotImplementedError


class Migration001_InitialSchema(Migration):
    """Initial schema setup - create collections and indexes."""

    version = "001"
    description = "Create initial schema with collections and indexes"

    def up(self, db: Database) -> None:
        """Apply initial schema migration."""
        logger.info("Applying migration 001: Initial schema")

        documents_indexes = [
            IndexModel([("filename", ASCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("processing_result.extractions.extractor", ASCENDING)]),
            IndexModel([("processing_result.processed_at", DESCENDING)], expireAfterSeconds=30 * 24 * 60 * 60),
            IndexModel([("user_id", ASCENDING)]),
        ]
        db.documents.create_indexes(documents_indexes)

        users_indexes = [
            IndexModel([("email", ASCENDING)], unique=True),
            IndexModel([("username", ASCENDING)], unique=True),
            IndexModel([("created_at", DESCENDING)]),
        ]
        db.users.create_indexes(users_indexes)

        analyses_indexes = [
            IndexModel([("document_id", ASCENDING)], unique=True),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("user_id", ASCENDING)]),
        ]
        db.analyses.create_indexes(analyses_indexes)

        logger.info("Initial schema migration completed")

    def down(self, db: Database) -> None:
        """Rollback initial schema migration."""
        logger.info("Rolling back migration 001")
        db.documents.drop_indexes()
        db.users.drop_indexes()
        db.analyses.drop_indexes()
        logger.info("Rollback completed")


class Migration002_AddUserTracking(Migration):
    """Add user tracking fields to documents."""

    version = "002"
    description = "Add user_id and ownership tracking to documents"

    def up(self, db: Database) -> None:
        """Add user tracking fields."""
        logger.info("Applying migration 002: Add user tracking")

        db.documents.update_many(
            {"user_id": {"$exists": False}},
            {"$set": {"user_id": None}}
        )

        db.documents.update_many(
            {"is_public": {"$exists": False}},
            {"$set": {"is_public": False}}
        )

        logger.info("User tracking migration completed")

    def down(self, db: Database) -> None:
        """Rollback user tracking fields."""
        logger.info("Rolling back migration 002")
        logger.info("Cannot rollback field additions safely")
        logger.info("Rollback skipped")


class Migration003_AddValidationCollection(Migration):
    """Create validation results collection."""

    version = "003"
    description = "Create validation results collection for quality tracking"

    def up(self, db: Database) -> None:
        """Create validation collection."""
        logger.info("Applying migration 003: Create validation collection")

        validation_indexes = [
            IndexModel([("document_id", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
            IndexModel([("overall_valid", ASCENDING)]),
        ]
        db.validations.create_indexes(validation_indexes)

        logger.info("Validation collection migration completed")

    def down(self, db: Database) -> None:
        """Drop validation collection."""
        logger.info("Rolling back migration 003")
        db.validations.drop()
        logger.info("Rollback completed")


class Migration004_AddProcessingHistory(Migration):
    """Add processing history tracking."""

    version = "004"
    description = "Add processing history for audit trail"

    def up(self, db: Database) -> None:
        """Add processing history fields."""
        logger.info("Applying migration 004: Add processing history")

        processing_history_indexes = [
            IndexModel([("document_id", ASCENDING)]),
            IndexModel([("step", ASCENDING)]),
            IndexModel([("started_at", DESCENDING)]),
        ]
        db.processing_history.create_indexes(processing_history_indexes)

        logger.info("Processing history migration completed")

    def down(self, db: Database) -> None:
        """Rollback processing history."""
        logger.info("Rolling back migration 004")
        db.processing_history.drop()
        logger.info("Rollback completed")


MIGRATIONS: List[Migration] = [
    Migration001_InitialSchema(),
    Migration002_AddUserTracking(),
    Migration003_AddValidationCollection(),
    Migration004_AddProcessingHistory(),
]


class MigrationManager:
    """Manages database migrations."""

    def __init__(self, db: Database):
        """Initialize migration manager."""
        self.db = db
        self._applied_migrations: List[str] = []

    @property
    def applied_migrations(self) -> List[str]:
        """Get list of applied migrations."""
        if not self._applied_migrations:
            self._load_applied_migrations()
        return self._applied_migrations

    def _load_applied_migrations(self) -> None:
        """Load applied migrations from database."""
        try:
            migrations_collection = self.db.migrations
            cursor = migrations_collection.find({}, {"version": 1})
            self._applied_migrations = [doc["version"] for doc in cursor]
        except Exception as e:
            logger.warning(f"Could not load migrations: {e}")
            self._applied_migrations = []

    def _record_migration(self, migration: Migration) -> None:
        """Record a migration as applied."""
        try:
            self.db.migrations.insert_one({
                "version": migration.version,
                "description": migration.description,
                "applied_at": datetime.utcnow(),
            })
            self._applied_migrations.append(migration.version)
        except Exception as e:
            logger.error(f"Failed to record migration: {e}")

    def _remove_migration_record(self, migration: Migration) -> None:
        """Remove migration record."""
        try:
            self.db.migrations.delete_one({"version": migration.version})
            if migration.version in self._applied_migrations:
                self._applied_migrations.remove(migration.version)
        except Exception as e:
            logger.error(f"Failed to remove migration record: {e}")

    def run_migrations(self, target_version: Optional[str] = None) -> Dict[str, Any]:
        """
        Run all pending migrations.

        Args:
            target_version: Optional version to migrate to (default: latest)

        Returns:
            Dict with migration results
        """
        results = {
            "applied": [],
            "skipped": [],
            "failed": [],
        }

        for migration in MIGRATIONS:
            if migration.version in self.applied_migrations:
                results["skipped"].append(migration.version)
                continue

            if target_version and migration.version > target_version:
                continue

            try:
                migration.up(self.db)
                self._record_migration(migration)
                results["applied"].append(migration.version)
                logger.info(f"Migration {migration.version} applied: {migration.description}")
            except Exception as e:
                logger.error(f"Migration {migration.version} failed: {e}")
                results["failed"].append({
                    "version": migration.version,
                    "error": str(e),
                })

        return results

    def rollback_migration(self, version: str) -> bool:
        """
        Rollback a specific migration.

        Args:
            version: Migration version to rollback

        Returns:
            True if successful, False otherwise
        """
        migration = next((m for m in MIGRATIONS if m.version == version), None)
        if not migration:
            logger.error(f"Migration {version} not found")
            return False

        if version not in self.applied_migrations:
            logger.error(f"Migration {version} not applied")
            return False

        try:
            migration.down(self.db)
            self._remove_migration_record(migration)
            logger.info(f"Migration {version} rolled back")
            return True
        except Exception as e:
            logger.error(f"Rollback of migration {version} failed: {e}")
            return False

    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status."""
        latest_migration = MIGRATIONS[-1] if MIGRATIONS else None

        return {
            "current_version": self.applied_migrations[-1] if self.applied_migrations else None,
            "latest_version": latest_migration.version if latest_migration else None,
            "pending_migrations": [
                m.version for m in MIGRATIONS
                if m.version not in self.applied_migrations
            ],
            "total_applied": len(self.applied_migrations),
            "total_pending": len([
                m for m in MIGRATIONS
                if m.version not in self.applied_migrations
            ]),
        }

    def create_indexes(self) -> Dict[str, int]:
        """Create all indexes for collections."""
        results = {"created": 0, "errors": 0}

        collections = {
            "documents": [
                ("filename", ASCENDING),
                ("status", ASCENDING),
                ("created_at", DESCENDING),
                ("user_id", ASCENDING),
            ],
            "users": [
                ("email", ASCENDING),
                ("username", ASCENDING),
                ("created_at", DESCENDING),
            ],
            "analyses": [
                ("document_id", ASCENDING),
                ("created_at", DESCENDING),
                ("user_id", ASCENDING),
            ],
        }

        for collection_name, indexes in collections.items():
            try:
                collection = getattr(self.db, collection_name)
                for field, direction in indexes:
                    collection.create_index([(field, direction)])
                    results["created"] += 1
            except Exception as e:
                logger.error(f"Error creating indexes for {collection_name}: {e}")
                results["errors"] += 1

        return results


async def run_migrations(db) -> Dict[str, Any]:
    """Run all pending database migrations."""
    manager = MigrationManager(db)
    return manager.run_migrations()
