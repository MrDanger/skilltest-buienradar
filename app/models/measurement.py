from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class StationMeasurement(Base):
    __tablename__ = "station_measurements"
    __table_args__ = (
        UniqueConstraint("stationid", "timestamp", name="uq_station_timestamp"),
        Index("ix_station_measurements_timestamp", "timestamp"),
        Index("ix_station_measurements_stationid", "stationid"),
    )

    measurementid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    groundtemperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    feeltemperature: Mapped[float | None] = mapped_column(Float, nullable=True)
    windgusts: Mapped[float | None] = mapped_column(Float, nullable=True)
    windspeed_bft: Mapped[int | None] = mapped_column(Integer, nullable=True)
    humidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    precipitation: Mapped[float | None] = mapped_column(Float, nullable=True)
    sunpower: Mapped[float | None] = mapped_column(Float, nullable=True)
    stationid: Mapped[int] = mapped_column(ForeignKey("weather_stations.stationid"), nullable=False)

    station = relationship("WeatherStation", back_populates="measurements")
