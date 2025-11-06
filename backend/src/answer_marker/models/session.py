"""Session models for the Answer Sheet Marker system.

This module defines data models for tracking marking sessions and progress.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime, timezone


class MarkingSession(BaseModel):
    """Marking session tracking.

    Represents a marking session with progress tracking, status management,
    and configuration storage.
    """

    session_id: str = Field(..., description="Unique session identifier")
    marking_guide_path: str
    answer_sheets_path: str
    output_path: str

    # Status
    status: Literal["initialized", "processing", "completed", "failed"] = "initialized"

    # Progress
    total_sheets: int = 0
    processed_sheets: int = 0
    failed_sheets: int = 0

    # Timing
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    # Results
    reports: List[str] = Field(default_factory=list, description="Paths to generated reports")

    # Configuration
    config: dict = Field(default_factory=dict, description="Session configuration")

    def update_progress(self, processed: int, failed: int = 0):
        """Update session progress.

        Args:
            processed: Number of sheets processed successfully
            failed: Number of sheets that failed processing
        """
        self.processed_sheets = processed
        self.failed_sheets = failed

        if self.processed_sheets + self.failed_sheets >= self.total_sheets:
            self.status = "completed"
            self.completed_at = datetime.now(timezone.utc)

    def get_progress_percentage(self) -> float:
        """Get progress as percentage.

        Returns:
            Progress percentage (0-100)
        """
        if self.total_sheets == 0:
            return 0.0
        return (self.processed_sheets + self.failed_sheets) / self.total_sheets * 100
