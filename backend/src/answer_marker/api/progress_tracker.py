"""Progress tracking for long-running operations using Server-Sent Events."""

import asyncio
from typing import Dict, Optional
from datetime import datetime
import json


class ProgressTracker:
    """Global progress tracker for SSE streaming."""

    def __init__(self):
        self._progress: Dict[str, Dict] = {}
        self._queues: Dict[str, asyncio.Queue] = {}

    def create_job(self, job_id: str, total_steps: int, job_type: str = "upload") -> None:
        """Initialize a new job for progress tracking."""
        self._progress[job_id] = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "initializing",
            "current_step": 0,
            "total_steps": total_steps,
            "message": "Initializing...",
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "error": None,
        }
        self._queues[job_id] = asyncio.Queue()

    async def update_progress(
        self,
        job_id: str,
        current_step: int,
        message: str,
        status: str = "processing",
    ) -> None:
        """Update progress for a job and notify subscribers."""
        if job_id not in self._progress:
            return

        self._progress[job_id].update({
            "current_step": current_step,
            "message": message,
            "status": status,
        })

        # Send update to SSE queue
        if job_id in self._queues:
            await self._queues[job_id].put(self._progress[job_id].copy())

    async def complete_job(self, job_id: str, message: str = "Completed") -> None:
        """Mark job as completed."""
        if job_id not in self._progress:
            return

        self._progress[job_id].update({
            "status": "completed",
            "message": message,
            "completed_at": datetime.now().isoformat(),
        })

        if job_id in self._queues:
            await self._queues[job_id].put(self._progress[job_id].copy())
            # Signal end of stream
            await self._queues[job_id].put(None)

    async def fail_job(self, job_id: str, error: str) -> None:
        """Mark job as failed."""
        if job_id not in self._progress:
            return

        self._progress[job_id].update({
            "status": "failed",
            "message": f"Error: {error}",
            "error": error,
            "completed_at": datetime.now().isoformat(),
        })

        if job_id in self._queues:
            await self._queues[job_id].put(self._progress[job_id].copy())
            await self._queues[job_id].put(None)

    async def get_progress_stream(self, job_id: str):
        """Get SSE stream for job progress."""
        if job_id not in self._queues:
            yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
            return

        queue = self._queues[job_id]

        try:
            while True:
                # Wait for next progress update
                progress = await queue.get()

                # None signals end of stream
                if progress is None:
                    break

                # Send SSE event
                yield f"data: {json.dumps(progress)}\n\n"

                # Clean up if completed or failed
                if progress.get("status") in ["completed", "failed"]:
                    break
        finally:
            # Cleanup
            if job_id in self._queues:
                del self._queues[job_id]
            if job_id in self._progress:
                del self._progress[job_id]

    def get_status(self, job_id: str) -> Optional[Dict]:
        """Get current status of a job."""
        return self._progress.get(job_id)


# Global progress tracker instance
progress_tracker = ProgressTracker()
