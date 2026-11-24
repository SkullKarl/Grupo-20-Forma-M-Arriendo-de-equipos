
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Equipment(Base):
    __tablename__ = "equipments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="available", nullable=False)

    reservations = relationship(
        "Reservation",
        back_populates="equipment"
    )


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)

    equipment_id = Column(
        Integer,
        ForeignKey("equipments.id"),
        nullable=False
    )

    # Identificador del arriendo que originó la reserva.
    # Es nullable para conservar las reservas antiguas.
    rental_id = Column(String, nullable=True, unique=True)

    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    status = Column(String, default="reserved", nullable=False)

    equipment = relationship(
        "Equipment",
        back_populates="reservations"
    )
