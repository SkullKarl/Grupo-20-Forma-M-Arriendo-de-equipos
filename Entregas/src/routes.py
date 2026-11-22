from database import session
from models import Deliveries
from sqlalchemy.exc import SQLAlchemyError
from schemas import ScheduleDeliveryRequest
from fastapi import APIRouter, HTTPException, status

router = APIRouter()

@router.post("/deliveries/schedule", status_code=status.HTTP_201_CREATED)
async def schedule_delivery(payload: ScheduleDeliveryRequest):
    existing_delivery = (session.query(Deliveries).filter(
            Deliveries.Equipment_Id == payload.Equipment_Id,
            Deliveries.Delivery_Date == payload.Delivery_Date,
            Deliveries.Status == "SCHEDULED",
        ).first())

    if existing_delivery:
        return {
            "status": "ALREADY_SCHEDULED",
            "message": "La entrega para este equipo ya estaba agendada.",
            "data": {
                "Delivery_Id": existing_delivery.Delivery_Id,
                "Equipment_Id": existing_delivery.Equipment_Id,
                "Delivery_Date": existing_delivery.Delivery_Date,
                "Status": existing_delivery.Status,
            },
        }

    try:
        new_delivery = Deliveries(
            Equipment_Id=payload.Equipment_Id,
            Delivery_Date=payload.Delivery_Date,
            Status="SCHEDULED",
        )
        session.add(new_delivery)
        session.commit()
        session.refresh(new_delivery)

        return {
            "status": "SUCCESS",
            "message": "Entrega agendada correctamente.",
            "data": {
                "Delivery_Id": new_delivery.Delivery_Id,
                "Equipment_Id": new_delivery.Equipment_Id,
                "Delivery_Date": new_delivery.Delivery_Date,
                "Status": new_delivery.Status,
            },
        }
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "FAILED",
                "message": "Error al agendar en la base de datos.",
                "error": str(e),
            },
        )

@router.get("/deliveries")
async def list_deliveries():
    deliveries = session.query(Deliveries).all()
    return {
        {
            "Delivery_Id": d.Delivery_Id,
            "Equipment_Id": d.Equipment_Id,
            "Delivery_Date": d.Delivery_Date,
            "Status": d.Status,
        }
        for d in deliveries
    }