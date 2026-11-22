from pydantic import BaseModel

class ScheduleDeliveryRequest(BaseModel):
    Equipment_Id: str
    Delivery_Date: str