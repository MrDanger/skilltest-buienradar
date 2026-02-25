from app.services.analytics import (
    average_temperature,
    highest_temperature_station,
    north_sea_station,
    station_biggest_feel_gap,
)
from app.services.ingestion import ingest_latest_payload

SAMPLE_PAYLOAD = {
    "actual": {
        "stationmeasurements": [
            {
                "stationid": 100,
                "stationname": "Station Alpha",
                "lat": 52.0,
                "lon": 5.0,
                "regio": "Utrecht",
                "timestamp": "2026-02-25T10:00:00",
                "temperature": 11.0,
                "groundtemperature": 10.0,
                "feeltemperature": 9.0,
                "windgusts": 7.0,
                "windspeedBft": 3,
                "humidity": 70.0,
                "precipitation": 0.0,
                "sunpower": 100.0,
            },
            {
                "stationid": 101,
                "stationname": "Station North Sea",
                "lat": 54.8,
                "lon": 4.7,
                "regio": "Noordzee",
                "timestamp": "2026-02-25T10:00:00",
                "temperature": 8.0,
                "groundtemperature": 7.0,
                "feeltemperature": 2.0,
                "windgusts": 14.0,
                "windspeedBft": 6,
                "humidity": 95.0,
                "precipitation": 0.0,
                "sunpower": 20.0,
            },
        ]
    }
}


def test_ingestion_and_analytics(db_session):
    result = ingest_latest_payload(db_session, SAMPLE_PAYLOAD)
    assert result.stations_upserted == 2
    assert result.measurements_inserted == 2

    highest = highest_temperature_station(db_session)
    assert highest is not None
    assert highest.stationname == "Station Alpha"

    avg = average_temperature(db_session)
    assert avg.average_temperature == 9.5

    gap = station_biggest_feel_gap(db_session)
    assert gap is not None
    assert gap.stationname == "Station North Sea"
    assert round(gap.temperature_gap, 2) == 6.0

    north = north_sea_station(db_session)
    assert north is not None
    assert north.stationname == "Station North Sea"


def test_idempotent_ingestion(db_session):
    first = ingest_latest_payload(db_session, SAMPLE_PAYLOAD)
    second = ingest_latest_payload(db_session, SAMPLE_PAYLOAD)

    assert first.measurements_inserted == 2
    assert second.measurements_inserted == 0
