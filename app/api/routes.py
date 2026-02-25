from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.response import (
    AverageTemperatureResponse,
    FeelGapResponse,
    HighestTemperatureResponse,
    IngestionResponse,
    NorthSeaStationResponse,
    SchedulerStatusResponse,
)
from app.services.analytics import (
    average_temperature,
    highest_temperature_station,
    north_sea_station,
    station_biggest_feel_gap,
    temperature_series,
)
from app.services.ingestion import ingest_latest
from app.services.scheduler import ingestion_scheduler

router = APIRouter(prefix="/api", tags=["weather"])


@router.post("/ingestion/once", response_model=IngestionResponse)
def ingest_once(db: Session = Depends(get_db)) -> IngestionResponse:
    return ingest_latest(db)


@router.get("/analysis/highest-temperature", response_model=HighestTemperatureResponse)
def get_highest_temperature(db: Session = Depends(get_db)) -> HighestTemperatureResponse:
    result = highest_temperature_station(db)
    if result is None:
        raise HTTPException(status_code=404, detail="No temperature data available")
    return result


@router.get("/analysis/average-temperature", response_model=AverageTemperatureResponse)
def get_average_temperature(db: Session = Depends(get_db)) -> AverageTemperatureResponse:
    return average_temperature(db)


@router.get("/analysis/biggest-feel-gap", response_model=FeelGapResponse)
def get_biggest_feel_gap(db: Session = Depends(get_db)) -> FeelGapResponse:
    result = station_biggest_feel_gap(db)
    if result is None:
        raise HTTPException(status_code=404, detail="No feel/actual temperature data available")
    return result


@router.get("/analysis/north-sea-station", response_model=NorthSeaStationResponse)
def get_north_sea_station(db: Session = Depends(get_db)) -> NorthSeaStationResponse:
    result = north_sea_station(db)
    if result is None:
        raise HTTPException(status_code=404, detail="North Sea station not found")
    return result


@router.get("/analysis/temperature-series")
def get_temperature_series(
    limit: int = Query(default=72, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict[str, list[dict[str, float | str]]]:
    return {"data": temperature_series(db, limit=limit)}


@router.get("/dashboard/summary")
def get_dashboard_summary(
    limit: int = Query(default=72, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    return {
        "highest_temperature": highest_temperature_station(db),
        "average_temperature": average_temperature(db),
        "biggest_feel_gap": station_biggest_feel_gap(db),
        "north_sea_station": north_sea_station(db),
        "temperature_series": temperature_series(db, limit=limit),
    }


@router.post("/scheduler/start", response_model=SchedulerStatusResponse)
def start_scheduler(minutes: int = Query(default=20, ge=1, le=180)) -> SchedulerStatusResponse:
    ingestion_scheduler.start(interval_minutes=minutes)
    return SchedulerStatusResponse(**ingestion_scheduler.status())


@router.post("/scheduler/stop", response_model=SchedulerStatusResponse)
def stop_scheduler() -> SchedulerStatusResponse:
    ingestion_scheduler.stop()
    return SchedulerStatusResponse(**ingestion_scheduler.status())


@router.get("/scheduler/status", response_model=SchedulerStatusResponse)
def scheduler_status() -> SchedulerStatusResponse:
    return SchedulerStatusResponse(**ingestion_scheduler.status())
