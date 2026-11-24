from typing import Optional
from pydantic import BaseModel

class RentalSagaRequest(BaseModel):
    Rental_Id: str
    Equipo_Id: str
    Buy_Order: str
    Session_Id: str
    Charge: float
    Start_Date: str
    End_Date: str
    Delivery_Date: str
    Idempotency_Key: Optional[str] = None

class SagaStepResult(BaseModel):
    step: str
    status: str
    detail: Optional[dict] = None

class RentalSagaResponse(BaseModel):
    saga_status: str
    message: str
    rental_id: str
    payment_token: Optional[str] = None
    steps: list[SagaStepResult]