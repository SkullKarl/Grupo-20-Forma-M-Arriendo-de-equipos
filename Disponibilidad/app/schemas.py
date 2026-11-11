from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

# Información para crear equipo
class EquipmentCreate(BaseModel):
    name: str = Field(min_length=2)
    description: str | None = None

# Respuesta al consultar equipo
class EquipmentResponse(BaseModel):
    id: int
    name: str
    description: str | None
    status: str

    model_config = ConfigDict(from_attributes=True)

# Información para crear reserva
class ReservationCreate(BaseModel):
    equipment_id: int
    start_date: datetime
    end_date: datetime

# Respuesta al consultar reserva
class ReservationResponse(BaseModel):
    id: int
    equipment_id: int
    start_date: datetime
    end_date: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)