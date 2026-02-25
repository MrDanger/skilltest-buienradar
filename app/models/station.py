from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WeatherStation(Base):
    __tablename__ = "weather_stations"

    stationid: Mapped[int] = mapped_column(Integer, primary_key=True)
    stationname: Mapped[str] = mapped_column(String(255), nullable=False)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    regio: Mapped[str | None] = mapped_column(String(255), nullable=True)

    measurements = relationship("StationMeasurement", back_populates="station", cascade="all,delete")
