from datetime import datetime

from pydantic import BaseModel


class IngestionResponse(BaseModel):
    fetched_at: datetime
    stations_upserted: int
    measurements_inserted: int


class HighestTemperatureResponse(BaseModel):
    stationid: int
    stationname: str
    timestamp: datetime
    temperature: float


class AverageTemperatureResponse(BaseModel):
    average_temperature: float | None


class FeelGapResponse(BaseModel):
    stationid: int
    stationname: str
    timestamp: datetime
    temperature: float
    feeltemperature: float
    temperature_gap: float


class NorthSeaStationResponse(BaseModel):
    stationid: int
    stationname: str
    regio: str | None
    lat: float | None
    lon: float | None


class SchedulerStatusResponse(BaseModel):
    active: bool
    interval_minutes: int | None
    next_run_time: datetime | None
