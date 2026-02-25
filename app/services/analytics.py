from sqlalchemy import Float, cast, func, select
from sqlalchemy.orm import Session

from app.models.measurement import StationMeasurement
from app.models.station import WeatherStation
from app.schemas.response import (
    AverageTemperatureResponse,
    FeelGapResponse,
    HighestTemperatureResponse,
    NorthSeaStationResponse,
)


def highest_temperature_station(db: Session) -> HighestTemperatureResponse | None:
    stmt = (
        select(
            WeatherStation.stationid,
            WeatherStation.stationname,
            StationMeasurement.timestamp,
            StationMeasurement.temperature,
        )
        .join(StationMeasurement, StationMeasurement.stationid == WeatherStation.stationid)
        .where(StationMeasurement.temperature.is_not(None))
        .order_by(StationMeasurement.temperature.desc())
        .limit(1)
    )
    row = db.execute(stmt).first()
    if row is None:
        return None
    return HighestTemperatureResponse(
        stationid=row.stationid,
        stationname=row.stationname,
        timestamp=row.timestamp,
        temperature=row.temperature,
    )


def average_temperature(db: Session) -> AverageTemperatureResponse:
    stmt = select(func.avg(StationMeasurement.temperature)).where(
        StationMeasurement.temperature.is_not(None)
    )
    avg_temp = db.execute(stmt).scalar_one_or_none()
    return AverageTemperatureResponse(
        average_temperature=float(avg_temp) if avg_temp is not None else None
    )


def station_biggest_feel_gap(db: Session) -> FeelGapResponse | None:
    gap_expr = func.abs(StationMeasurement.feeltemperature - StationMeasurement.temperature)
    stmt = (
        select(
            WeatherStation.stationid,
            WeatherStation.stationname,
            StationMeasurement.timestamp,
            StationMeasurement.temperature,
            StationMeasurement.feeltemperature,
            gap_expr.label("temperature_gap"),
        )
        .join(StationMeasurement, StationMeasurement.stationid == WeatherStation.stationid)
        .where(StationMeasurement.temperature.is_not(None))
        .where(StationMeasurement.feeltemperature.is_not(None))
        .order_by(gap_expr.desc())
        .limit(1)
    )
    row = db.execute(stmt).first()
    if row is None:
        return None
    return FeelGapResponse(
        stationid=row.stationid,
        stationname=row.stationname,
        timestamp=row.timestamp,
        temperature=row.temperature,
        feeltemperature=row.feeltemperature,
        temperature_gap=row.temperature_gap,
    )


def north_sea_station(db: Session) -> NorthSeaStationResponse | None:
    stmt = (
        select(
            WeatherStation.stationid,
            WeatherStation.stationname,
            WeatherStation.regio,
            WeatherStation.lat,
            WeatherStation.lon,
        )
        .where(func.lower(WeatherStation.regio).contains("noordzee"))
        .limit(1)
    )
    row = db.execute(stmt).first()
    if row is None:
        return None
    return NorthSeaStationResponse(
        stationid=row.stationid,
        stationname=row.stationname,
        regio=row.regio,
        lat=row.lat,
        lon=row.lon,
    )


def temperature_series(db: Session, limit: int = 72) -> list[dict[str, float | str]]:
    stmt = (
        select(
            StationMeasurement.timestamp,
            func.avg(cast(StationMeasurement.temperature, Float)).label("avg_temperature"),
        )
        .where(StationMeasurement.temperature.is_not(None))
        .group_by(StationMeasurement.timestamp)
        .order_by(StationMeasurement.timestamp.desc())
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    data = [
        {
            "timestamp": row.timestamp.isoformat(timespec="minutes"),
            "avg_temperature": round(float(row.avg_temperature), 2),
        }
        for row in rows
        if row.avg_temperature is not None
    ]
    data.reverse()
    return data
