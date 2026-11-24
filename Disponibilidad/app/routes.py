
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter()


def crear_reserva(reservation, db: Session):
    if reservation.start_date >= reservation.end_date:
        raise HTTPException(
            status_code=400,
            detail="La fecha inicial debe ser anterior a la fecha final"
        )

    equipment = db.query(models.Equipment).filter(
        models.Equipment.id == reservation.equipment_id
    ).first()

    if equipment is None:
        raise HTTPException(
            status_code=404,
            detail="El equipo solicitado no existe"
        )

    if getattr(reservation, "rental_id", None):
        existing_rental = db.query(models.Reservation).filter(
            models.Reservation.rental_id == reservation.rental_id
        ).first()

        if existing_rental:
            return existing_rental

    overlapping = db.query(models.Reservation).filter(
        models.Reservation.equipment_id == reservation.equipment_id,
        models.Reservation.status == "reserved",
        models.Reservation.start_date < reservation.end_date,
        models.Reservation.end_date > reservation.start_date
    ).first()

    if overlapping:
        raise HTTPException(
            status_code=409,
            detail="El equipo ya está reservado durante el periodo"
        )

    new_reservation = models.Reservation(
        equipment_id=reservation.equipment_id,
        rental_id=getattr(reservation, "rental_id", None),
        start_date=reservation.start_date,
        end_date=reservation.end_date,
        status="reserved"
    )

    db.add(new_reservation)
    db.commit()
    db.refresh(new_reservation)

    return new_reservation


@router.post(
    "/equipments",
    response_model=schemas.EquipmentResponse,
    status_code=201
)
def create_equipment(
    equipment: schemas.EquipmentCreate,
    db: Session = Depends(get_db)
):
    new_equipment = models.Equipment(
        name=equipment.name,
        description=equipment.description
    )

    db.add(new_equipment)
    db.commit()
    db.refresh(new_equipment)

    return new_equipment


@router.get(
    "/equipments",
    response_model=list[schemas.EquipmentResponse]
)
def list_equipments(db: Session = Depends(get_db)):
    return db.query(models.Equipment).all()


@router.post(
    "/reservations",
    response_model=schemas.ReservationResponse,
    status_code=201
)
def create_reservation(
    reservation: schemas.ReservationCreate,
    db: Session = Depends(get_db)
):
    return crear_reserva(reservation, db)


@router.get(
    "/reservations",
    response_model=list[schemas.ReservationResponse]
)
def list_reservations(db: Session = Depends(get_db)):
    return db.query(models.Reservation).all()


# Operación utilizada por el flujo de Saga.
@router.post(
    "/availability/reserve",
    response_model=schemas.ReservationResponse,
    status_code=201
)
def reserve_for_rental(
    reservation: schemas.SagaReservationCreate,
    db: Session = Depends(get_db)
):
    return crear_reserva(reservation, db)


# Compensación: liberar la reserva de un arriendo específico.
@router.post("/availability/release")
def release_reservation(
    payload: schemas.ReservationRelease,
    db: Session = Depends(get_db)
):
    reservation = db.query(models.Reservation).filter(
        models.Reservation.rental_id == payload.rental_id
    ).first()

    if reservation is None:
        raise HTTPException(
            status_code=404,
            detail="No existe una reserva para ese arriendo"
        )

    if reservation.status == "released":
        return {
            "status": "ALREADY_RELEASED",
            "rental_id": payload.rental_id
        }

    reservation.status = "released"
    db.commit()

    return {
        "status": "RELEASED",
        "rental_id": payload.rental_id,
        "reservation_id": reservation.id
    }
