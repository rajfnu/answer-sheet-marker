"""Persistent storage with file hash-based caching for marking guides and reports.

This module provides persistent storage that survives server restarts and
implements hash-based caching to avoid re-processing identical files.
"""

import json
import pickle
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
from loguru import logger
import hashlib

from answer_marker.models.marking_guide import MarkingGuide
from answer_marker.models.report import EvaluationReport


class PersistentStorage:
    """Persistent storage for marking guides and reports with hash-based caching."""

    def __init__(self, storage_dir: Path):
        """Initialize persistent storage.

        Args:
            storage_dir: Directory to store persistent data
        """
        self.storage_dir = Path(storage_dir)
        self.guides_dir = self.storage_dir / "marking_guides"
        self.reports_dir = self.storage_dir / "reports"
        self.cache_dir = self.storage_dir / "cache"
        self.metadata_file = self.storage_dir / "metadata.json"

        # Create directories
        self.guides_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize metadata
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """Load metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}")
                return {
                    "file_hashes": {},
                    "guides": {},
                    "reports": {},
                    "answer_sheet_hashes": {},
                }
        return {
            "file_hashes": {},
            "guides": {},
            "reports": {},
            "answer_sheet_hashes": {},
        }

    def _save_metadata(self):
        """Save metadata to disk."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    def compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of a file.

        Args:
            file_path: Path to the file

        Returns:
            Hex digest of the file hash
        """
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def check_cache(self, file_path: Path) -> Optional[str]:
        """Check if a file has been processed before based on its hash.

        Args:
            file_path: Path to the file to check

        Returns:
            Guide ID if file was processed before, None otherwise
        """
        file_hash = self.compute_file_hash(file_path)
        cached_guide_id = self.metadata["file_hashes"].get(file_hash)

        if cached_guide_id:
            logger.info(f"Cache hit for file hash {file_hash[:8]}... -> {cached_guide_id}")
            return cached_guide_id

        logger.debug(f"Cache miss for file hash {file_hash[:8]}...")
        return None

    def save_marking_guide(
        self, guide_id: str, marking_guide: MarkingGuide, file_path: Path
    ) -> None:
        """Save a marking guide to persistent storage.

        Args:
            guide_id: Unique identifier for the guide
            marking_guide: MarkingGuide object to save
            file_path: Original file path (for hash caching)
        """
        try:
            # Save the marking guide
            guide_file = self.guides_dir / f"{guide_id}.pkl"
            with open(guide_file, "wb") as f:
                pickle.dump(marking_guide, f)

            # Update metadata
            file_hash = self.compute_file_hash(file_path)
            self.metadata["file_hashes"][file_hash] = guide_id
            self.metadata["guides"][guide_id] = {
                "title": marking_guide.title,
                "file_hash": file_hash,
                "created_at": datetime.now().isoformat(),
                "total_marks": float(marking_guide.total_marks),
                "num_questions": len(marking_guide.questions),
            }
            self._save_metadata()

            logger.info(f"Saved marking guide {guide_id} to persistent storage")

        except Exception as e:
            logger.error(f"Failed to save marking guide {guide_id}: {e}")
            raise

    def load_marking_guide(self, guide_id: str) -> Optional[MarkingGuide]:
        """Load a marking guide from persistent storage.

        Args:
            guide_id: Unique identifier for the guide

        Returns:
            MarkingGuide object if found, None otherwise
        """
        try:
            guide_file = self.guides_dir / f"{guide_id}.pkl"
            if not guide_file.exists():
                return None

            with open(guide_file, "rb") as f:
                marking_guide = pickle.load(f)

            logger.info(f"Loaded marking guide {guide_id} from persistent storage")
            return marking_guide

        except Exception as e:
            logger.error(f"Failed to load marking guide {guide_id}: {e}")
            return None

    def save_report(self, report_id: str, report: EvaluationReport, marking_guide_id: str) -> None:
        """Save a marking report to persistent storage.

        Args:
            report_id: Unique identifier for the report
            report: EvaluationReport object to save
            marking_guide_id: ID of the marking guide used
        """
        try:
            # Save the report
            report_file = self.reports_dir / f"{report_id}.pkl"
            with open(report_file, "wb") as f:
                pickle.dump(report, f)

            # Update metadata
            self.metadata["reports"][report_id] = {
                "student_id": report.student_id,
                "marking_guide_id": marking_guide_id,
                "assessment_title": report.assessment_title,
                "created_at": datetime.now().isoformat(),
                "total_marks": float(report.scoring_result.total_marks),
                "max_marks": float(report.scoring_result.max_marks),
                "percentage": float(report.scoring_result.percentage),
                "grade": report.scoring_result.grade,
                "passed": report.scoring_result.passed,
            }
            self._save_metadata()

            logger.info(f"Saved report {report_id} to persistent storage")

        except Exception as e:
            logger.error(f"Failed to save report {report_id}: {e}")
            raise

    def load_report(self, report_id: str) -> Optional[EvaluationReport]:
        """Load a report from persistent storage.

        Args:
            report_id: Unique identifier for the report

        Returns:
            EvaluationReport object if found, None otherwise
        """
        try:
            report_file = self.reports_dir / f"{report_id}.pkl"
            if not report_file.exists():
                return None

            with open(report_file, "rb") as f:
                report = pickle.load(f)

            logger.info(f"Loaded report {report_id} from persistent storage")
            return report

        except Exception as e:
            logger.error(f"Failed to load report {report_id}: {e}")
            return None

    def list_marking_guides(self) -> List[str]:
        """List all marking guide IDs in storage."""
        return list(self.metadata["guides"].keys())

    def list_reports(self) -> List[str]:
        """List all report IDs in storage."""
        return list(self.metadata["reports"].keys())

    def get_guide_metadata(self, guide_id: str) -> Optional[Dict]:
        """Get metadata for a marking guide."""
        return self.metadata["guides"].get(guide_id)

    def get_report_metadata(self, report_id: str) -> Optional[Dict]:
        """Get metadata for a report."""
        return self.metadata["reports"].get(report_id)

    def load_all_to_memory(self) -> tuple[Dict[str, MarkingGuide], Dict[str, EvaluationReport]]:
        """Load all marking guides and reports from disk to memory.

        Returns:
            Tuple of (marking_guides_dict, reports_dict)
        """
        marking_guides = {}
        reports = {}

        # Load all marking guides
        for guide_id in self.list_marking_guides():
            guide = self.load_marking_guide(guide_id)
            if guide:
                marking_guides[guide_id] = guide

        # Load all reports
        for report_id in self.list_reports():
            report = self.load_report(report_id)
            if report:
                reports[report_id] = report

        logger.info(
            f"Loaded {len(marking_guides)} marking guides and {len(reports)} reports from storage"
        )
        return marking_guides, reports

    def check_answer_sheet_cache(
        self, marking_guide_id: str, student_id: str, answer_sheet_path: Path
    ) -> Optional[str]:
        """Check if this exact answer sheet has already been marked.

        Args:
            marking_guide_id: ID of the marking guide
            student_id: Student identifier
            answer_sheet_path: Path to the answer sheet file

        Returns:
            Report ID if already marked, None otherwise
        """
        # Compute answer sheet hash
        answer_sheet_hash = self.compute_file_hash(answer_sheet_path)

        # Create cache key: guide_id + student_id + file_hash
        cache_key = f"{marking_guide_id}:{student_id}:{answer_sheet_hash}"

        cached_report_id = self.metadata["answer_sheet_hashes"].get(cache_key)

        if cached_report_id:
            logger.info(
                f"Cache hit for answer sheet: {student_id} + {marking_guide_id[:8]}... "
                f"-> {cached_report_id}"
            )
            return cached_report_id

        logger.debug(f"Cache miss for answer sheet: {student_id} + {marking_guide_id[:8]}...")
        return None

    def register_answer_sheet(
        self,
        marking_guide_id: str,
        student_id: str,
        answer_sheet_path: Path,
        report_id: str,
    ):
        """Register an answer sheet as having been marked.

        Args:
            marking_guide_id: ID of the marking guide used
            student_id: Student identifier
            answer_sheet_path: Path to the answer sheet file
            report_id: ID of the generated report
        """
        answer_sheet_hash = self.compute_file_hash(answer_sheet_path)
        cache_key = f"{marking_guide_id}:{student_id}:{answer_sheet_hash}"

        self.metadata["answer_sheet_hashes"][cache_key] = report_id
        self._save_metadata()

        logger.debug(f"Registered answer sheet in cache: {cache_key} -> {report_id}")
