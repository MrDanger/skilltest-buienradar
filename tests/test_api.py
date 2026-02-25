from app.services.ingestion import BuienradarClient

SAMPLE_PAYLOAD = {
    "actual": {
        "stationmeasurements": [
            {
                "stationid": 200,
                "stationname": "Rotterdam",
                "lat": 51.95,
                "lon": 4.45,
                "regio": "Rotterdam",
                "timestamp": "2026-02-25T11:00:00",
                "temperature": 14.0,
                "groundtemperature": 14.5,
                "feeltemperature": 12.8,
                "windgusts": 8.0,
                "windspeedBft": 4,
                "humidity": 75.0,
                "precipitation": 0.1,
                "sunpower": 300.0,
            },
            {
                "stationid": 201,
                "stationname": "Zeeplatform F-3",
                "lat": 54.85,
                "lon": 4.73,
                "regio": "Noordzee",
                "timestamp": "2026-02-25T11:00:00",
                "temperature": 7.0,
                "groundtemperature": 7.1,
                "feeltemperature": 2.1,
                "windgusts": 14.2,
                "windspeedBft": 6,
                "humidity": 99.0,
                "precipitation": 0.0,
                "sunpower": 10.0,
            },
        ]
    }
}


def test_ingestion_endpoint(client, monkeypatch):
    monkeypatch.setattr(BuienradarClient, "fetch_latest", lambda self: SAMPLE_PAYLOAD)

    response = client.post("/api/ingestion/once")
    assert response.status_code == 200
    data = response.json()
    assert data["measurements_inserted"] == 2


def test_analysis_endpoints(client, monkeypatch):
    monkeypatch.setattr(BuienradarClient, "fetch_latest", lambda self: SAMPLE_PAYLOAD)
    client.post("/api/ingestion/once")

    highest = client.get("/api/analysis/highest-temperature")
    assert highest.status_code == 200
    assert highest.json()["stationname"] == "Rotterdam"

    average = client.get("/api/analysis/average-temperature")
    assert average.status_code == 200
    assert round(average.json()["average_temperature"], 2) == 10.5

    north = client.get("/api/analysis/north-sea-station")
    assert north.status_code == 200
    assert "Noordzee" in north.json()["regio"]

    series = client.get("/api/analysis/temperature-series?limit=10")
    assert series.status_code == 200
    assert len(series.json()["data"]) == 1

    summary = client.get("/api/dashboard/summary?limit=10")
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["highest_temperature"]["stationname"] == "Rotterdam"
    assert len(payload["temperature_series"]) == 1


def test_scheduler_endpoints(client):
    start = client.post("/api/scheduler/start?minutes=5")
    assert start.status_code == 200
    assert start.json()["active"] is True
    assert start.json()["interval_minutes"] == 5

    status = client.get("/api/scheduler/status")
    assert status.status_code == 200
    assert status.json()["active"] is True

    stop = client.post("/api/scheduler/stop")
    assert stop.status_code == 200
    assert stop.json()["active"] is False
