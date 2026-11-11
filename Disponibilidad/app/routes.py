from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter()

# REGISTRAR EQUIPO

@router.post(
    "/equipments",
    response_model = schemas.EquipmentResponse,
    status_code = 201
)

def create_equipment(
    equipment: schemas.EquipmentCreate,
    db: Session = Depends(get_db)
):
    new_equipment = models.Equipment(
        name = equipment.name,
        description = equipment.description
    )

    db.add(new_equipment)
    db.commit()
    db.refresh(new_equipment)

    return new_equipment


# LISTAR TODOS LOS EQUIPOS

@router.get(
    "/equipments",
    response_model = list[schemas.EquipmentResponse]
)
def list_equipments(
    db: Session = Depends(get_db)
):

    equipments = db.query(models.Equipment).all()

    return equipments


# CREAR RESERVA

@router.post(
    "/reservations",
    response_model = schemas.ReservationResponse,
    status_code = 201
)
def create_reservation(
    reservation: schemas.ReservationCreate,
    db: Session = Depends(get_db)
):

    # Fecha inicial debe ser anterior a la final
    if reservation.start_date >= reservation.end_date:
        raise HTTPException(
            status_code = 400,
            detail = "La fecha inicial debe ser anterior a la fecha final"
        )

    # Equipo debe existir
    equipment = db.query(models.Equipment).filter(
        models.Equipment.id == reservation.equipment_id
    ).first()

    if equipment is None:
        raise HTTPException(
            status_code = 404,
            detail = "El equipo solicitado no existe"
        )

    # Buscar otra reserva activa
    overlapping_reservation = db.query(models.Reservation).filter(
        models.Reservation.equipment_id == reservation.equipment_id,
        models.Reservation.status == "reserved",
        models.Reservation.start_date < reservation.end_date, 
        models.Reservation.end_date > reservation.start_date
    ).first()

    if overlapping_reservation:
        raise HTTPException(
            status_code = 409,
            detail = "El equipo ya está reservado durante el periodo"
        )

    # Si no existe problema, creamos la reserva
    new_reservation = models.Reservation(
        equipment_id = reservation.equipment_id,
        start_date = reservation.start_date,
        end_date = reservation.end_date
    )

    db.add(new_reservation)
    db.commit()
    db.refresh(new_reservation)

    return new_reservation


# LISTAR LAS RESERVAS

@router.get(
    "/reservations",
    response_model = list[schemas.ReservationResponse]
)
def list_reservations(
    db: Session = Depends(get_db)
):
    reservations = db.query(models.Reservation).all()

    return reservations