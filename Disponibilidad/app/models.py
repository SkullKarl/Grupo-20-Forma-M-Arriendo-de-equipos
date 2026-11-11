from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base

# RELACIÓN 1:N ENTRE EQUIPOS Y RESERVAS, UN EQUIPO PUEDE TENER VARIAS RESERVAS

# Modelo para equipos disponibles
class Equipment(Base):
    __tablename__ = "equipments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="available", nullable=False)

    # Relación entre equipo y reservas
    reservations = relationship(
        "Reservation",
        back_populates = "equipment"
    )


# Modelo para reservas de equipos
class Reservation(Base):
    __tablename__ = "reservations"
    
    id = Column(Integer, primary_key=True, index=True)

    # Identificador equipo
    equipment_id = Column(
        Integer,
        ForeignKey("equipments.id"),
        nullable = False
    )

    # Periodo reserva
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    #Estado reserva
    status = Column(String, default="reserverd", nullable=False)

    # Relación con equipo
    equipment = relationship(
        "Equipment",
        back_populates = "reservations"
    )