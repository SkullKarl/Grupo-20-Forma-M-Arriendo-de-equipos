from pydantic import BaseModel

class ChargeRequest(BaseModel):
    Equipo_Id: str
    Buy_Order: str
    Session_Id: str
    Charge: float

class RefundRequest(BaseModel):
    Equipo_Id: str
    Charge: float
    Token: str