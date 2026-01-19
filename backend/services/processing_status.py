from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from bson import ObjectId


class ProcessingStatus(str, Enum):
    """Document processing status states."""

    PENDING = "pending"
    UPLOADED = "uploaded"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    ERROR = "error"


class ExtractorStatus(BaseModel):
    """Status of individual extractor."""

    extractor: str
    status: ProcessingStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    confidence: Optional[float] = None
    error: Optional[str] = None


class ProcessingStep(BaseModel):
    """A step in the document processing pipeline."""

    step: str
    status: ProcessingStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


class ProcessingHistory(BaseModel):
    """Processing history for a document."""

    document_id: str
    steps: List[ProcessingStep] = []
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_duration_ms: Optional[int] = None


class DocumentProcessingStatus(BaseModel):
    """Complete processing status for a document."""

    id: str
    filename: str
    status: ProcessingStatus
    progress_percentage: int = 0
    current_step: Optional[str] = None
    extractor_statuses: List[ExtractorStatus] = []
    history: Optional[ProcessingHistory] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class ProcessingStatusTracker:
    """Tracks document processing status throughout the pipeline."""

    def __init__(self):
        self._status_cache: Dict[str, DocumentProcessingStatus] = {}

    def create_status(
        self,
        document_id: str,
        filename: str,
        created_at: datetime = None,
    ) -> DocumentProcessingStatus:
        """Create initial processing status for a document."""
        status = DocumentProcessingStatus(
            id=document_id,
            filename=filename,
            status=ProcessingStatus.PENDING,
            progress_percentage=0,
            created_at=created_at or datetime.now(),
            updated_at=datetime.now(),
        )
        self._status_cache[document_id] = status
        return status

    def update_status(
        self,
        document_id: str,
        status: ProcessingStatus,
        progress_percentage: int = None,
        current_step: str = None,
        error: str = None,
    ) -> Optional[DocumentProcessingStatus]:
        """Update processing status."""
        if document_id not in self._status_cache:
            return None

        doc_status = self._status_cache[document_id]
        doc_status.status = status
        doc_status.updated_at = datetime.now()

        if progress_percentage is not None:
            doc_status.progress_percentage = progress_percentage
        if current_step is not None:
            doc_status.current_step = current_step
        if error is not None:
            doc_status.error = error

        if status == ProcessingStatus.COMPLETED:
            doc_status.completed_at = datetime.now()

        return doc_status

    def add_extractor_status(
        self,
        document_id: str,
        extractor: str,
        status: ProcessingStatus,
        confidence: float = None,
        error: str = None,
    ) -> Optional[ExtractorStatus]:
        """Add or update extractor status."""
        if document_id not in self._status_cache:
            return None

        doc_status = self._status_cache[document_id]

        existing = next(
            (e for e in doc_status.extractor_statuses if e.extractor == extractor),
            None,
        )

        if existing:
            existing.status = status
            existing.confidence = confidence
            existing.error = error
            existing.completed_at = (
                datetime.now() if status in [ProcessingStatus.COMPLETED, ProcessingStatus.ERROR] else None
            )
            return existing

        new_extractor = ExtractorStatus(
            extractor=extractor,
            status=status,
            started_at=datetime.now(),
            confidence=confidence,
            error=error,
            completed_at=(
                datetime.now() if status in [ProcessingStatus.COMPLETED, ProcessingStatus.ERROR] else None
            ),
        )
        doc_status.extractor_statuses.append(new_extractor)
        return new_extractor

    def start_extractor(self, document_id: str, extractor: str) -> Optional[ExtractorStatus]:
        """Mark extractor as started."""
        return self.add_extractor_status(
            document_id, extractor, ProcessingStatus.EXTRACTING
        )

    def complete_extractor(
        self, document_id: str, extractor: str, confidence: float
    ) -> Optional[ExtractorStatus]:
        """Mark extractor as completed."""
        return self.add_extractor_status(
            document_id, extractor, ProcessingStatus.COMPLETED, confidence=confidence
        )

    def fail_extractor(self, document_id: str, extractor: str, error: str) -> Optional[ExtractorStatus]:
        """Mark extractor as failed."""
        return self.add_extractor_status(
            document_id, extractor, ProcessingStatus.ERROR, error=error
        )

    def add_history_step(
        self,
        document_id: str,
        step: str,
        status: ProcessingStatus,
        details: Dict[str, Any] = None,
    ) -> Optional[ProcessingStep]:
        """Add a step to processing history."""
        if document_id not in self._status_cache:
            return None

        doc_status = self._status_cache[document_id]

        if doc_status.history is None:
            doc_status.history = ProcessingHistory(
                document_id=document_id,
                started_at=doc_status.created_at,
            )

        new_step = ProcessingStep(
            step=step,
            status=status,
            started_at=datetime.now(),
            details=details,
        )
        doc_status.history.steps.append(new_step)

        if status == ProcessingStatus.COMPLETED:
            new_step.completed_at = datetime.now()
            if doc_status.history.steps:
                previous = doc_status.history.steps[-2] if len(doc_status.history.steps) > 1 else None
                if previous and previous.completed_at:
                    new_step.duration_ms = int(
                        (new_step.completed_at - previous.completed_at).total_seconds() * 1000
                    )

        self._update_progress(document_id)
        return new_step

    def _update_progress(self, document_id: str):
        """Update overall progress percentage."""
        if document_id not in self._status_cache:
            return

        doc_status = self._status_cache[document_id]

        if not doc_status.history or not doc_status.history.steps:
            return

        completed_steps = sum(
            1 for s in doc_status.history.steps
            if s.status == ProcessingStatus.COMPLETED
        )
        total_steps = len(doc_status.history.steps)

        if total_steps > 0:
            doc_status.progress_percentage = int((completed_steps / total_steps) * 100)
            doc_status.current_step = doc_status.history.steps[-1].step

    def get_status(self, document_id: str) -> Optional[DocumentProcessingStatus]:
        """Get current processing status."""
        return self._status_cache.get(document_id)

    def finalize_status(
        self, document_id: str, success: bool = True, error: str = None
    ) -> Optional[DocumentProcessingStatus]:
        """Finalize processing status."""
        if document_id not in self._status_cache:
            return None

        doc_status = self._status_cache[document_id]

        if success:
            doc_status.status = ProcessingStatus.COMPLETED
            doc_status.progress_percentage = 100
        else:
            doc_status.status = ProcessingStatus.ERROR
            doc_status.error = error

        doc_status.completed_at = datetime.now()
        doc_status.updated_at = datetime.now()

        if doc_status.history:
            doc_status.history.completed_at = datetime.now()
            if doc_status.history.started_at and doc_status.completed_at:
                doc_status.history.total_duration_ms = int(
                    (doc_status.completed_at - doc_status.history.started_at).total_seconds() * 1000
                )

        return doc_status

    def remove_status(self, document_id: str):
        """Remove status from cache."""
        if document_id in self._status_cache:
            del self._status_cache[document_id]

    def get_all_statuses(self) -> List[DocumentProcessingStatus]:
        """Get all cached statuses."""
        return list(self._status_cache.values())

   (self) -> Dict:
        """Get summary def get_status_summary of all processing statuses."""
        statuses = self.get_all_statuses()

        by_status = {status: 0 for status in ProcessingStatus}
        for status in statuses:
            by_status[status.status] += 1

        return {
            "total_documents": len(statuses),
            "by_status": by_status,
            "average_progress": (
                sum(s.progress_percentage for s in statuses) / len(statuses)
                if statuses else 0
            ),
        }


tracker = ProcessingStatusTracker()
