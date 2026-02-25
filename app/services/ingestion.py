from datetime import datetime, timezone
from typing import Any

from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.models.measurement import StationMeasurement
from app.models.station import WeatherStation
from app.schemas.response import IngestionResponse
from app.services.buienradar_client import BuienradarClient


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def ingest_latest_payload(db: Session, payload: dict[str, Any]) -> IngestionResponse:
    measurements_raw = (
        payload.get("actual", {}).get("stationmeasurements", []) if isinstance(payload, dict) else []
    )
    if not isinstance(measurements_raw, list):
        raise ValueError("stationmeasurements is not a list")

    stations_upserted = 0
    measurement_rows: list[dict[str, Any]] = []

    for raw in measurements_raw:
        if not isinstance(raw, dict):
            continue

        stationid = _safe_int(raw.get("stationid"))
        timestamp = _safe_timestamp(raw.get("timestamp"))
        if stationid is None or timestamp is None:
            continue

        station_values = {
            "stationid": stationid,
            "stationname": str(raw.get("stationname") or f"Station {stationid}"),
            "lat": _safe_float(raw.get("lat")),
            "lon": _safe_float(raw.get("lon")),
            "regio": str(raw.get("regio")) if raw.get("regio") is not None else None,
        }
        station_stmt = insert(WeatherStation).values(**station_values)
        station_stmt = station_stmt.on_conflict_do_update(
            index_elements=[WeatherStation.stationid],
            set_={
                "stationname": station_values["stationname"],
                "lat": station_values["lat"],
                "lon": station_values["lon"],
                "regio": station_values["regio"],
            },
        )
        db.execute(station_stmt)
        stations_upserted += 1

        measurement_rows.append(
            {
                "stationid": stationid,
                "timestamp": timestamp,
                "temperature": _safe_float(raw.get("temperature")),
                "groundtemperature": _safe_float(raw.get("groundtemperature")),
                "feeltemperature": _safe_float(raw.get("feeltemperature")),
                "windgusts": _safe_float(raw.get("windgusts")),
                "windspeed_bft": _safe_int(raw.get("windspeedBft")),
                "humidity": _safe_float(raw.get("humidity")),
                "precipitation": _safe_float(raw.get("precipitation")),
                "sunpower": _safe_float(raw.get("sunpower")),
            }
        )

    measurements_inserted = 0
    if measurement_rows:
        measurement_stmt = insert(StationMeasurement).values(measurement_rows)
        measurement_stmt = measurement_stmt.on_conflict_do_nothing(
            index_elements=[StationMeasurement.stationid, StationMeasurement.timestamp]
        )
        result = db.execute(measurement_stmt)
        measurements_inserted = result.rowcount if result.rowcount is not None else 0

    db.commit()
    return IngestionResponse(
        fetched_at=datetime.now(timezone.utc),
        stations_upserted=stations_upserted,
        measurements_inserted=measurements_inserted,
    )


def ingest_latest(db: Session, client: BuienradarClient | None = None) -> IngestionResponse:
    weather_client = client or BuienradarClient()
    payload = weather_client.fetch_latest()
    return ingest_latest_payload(db, dict(payload))
