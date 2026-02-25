from datetime import datetime
from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.ingestion import ingest_latest

_JOB_ID = "weather_ingestion_job"


class IngestionSchedulerService:
    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler(timezone="UTC")
        self._lock = Lock()
        self._interval_minutes: int | None = None

    def _run_ingestion(self) -> None:
        db = SessionLocal()
        try:
            ingest_latest(db)
        except Exception:
            db.rollback()
        finally:
            db.close()

    def start(self, interval_minutes: int | None = None) -> None:
        settings = get_settings()
        interval = interval_minutes or settings.scheduler_default_interval_minutes
        interval = max(1, interval)

        with self._lock:
            if not self.scheduler.running:
                self.scheduler.start()

            self.scheduler.add_job(
                self._run_ingestion,
                "interval",
                minutes=interval,
                id=_JOB_ID,
                replace_existing=True,
                coalesce=True,
                max_instances=1,
                misfire_grace_time=60,
            )
            self._interval_minutes = interval

    def stop(self) -> None:
        with self._lock:
            if self.scheduler.running and self.scheduler.get_job(_JOB_ID):
                self.scheduler.remove_job(_JOB_ID)

    def shutdown(self) -> None:
        with self._lock:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=False)

    def status(self) -> dict[str, datetime | int | bool | None]:
        job = self.scheduler.get_job(_JOB_ID) if self.scheduler.running else None
        return {
            "active": job is not None,
            "interval_minutes": self._interval_minutes if job else None,
            "next_run_time": job.next_run_time if job else None,
        }


ingestion_scheduler = IngestionSchedulerService()
