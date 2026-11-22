import os
import asyncio
from typing import Optional
from database import session
from sqlalchemy.exc import SQLAlchemyError
from schemas import ChargeRequest, RefundRequest
from models import ChargeRequests, RefundRequests
from fastapi import APIRouter, Header, HTTPException, status

router = APIRouter()

@router.post("/payments/charge")
async def charge_payment(payload: ChargeRequest, idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
):
    key = idempotency_key or payload.Buy_Order
    existing_payment = (session.query(ChargeRequests).filter(ChargeRequests.Idempotency_Key == key).first())

    if existing_payment:
        print(f"La orden {key} ya fue procesada. Retornando respuesta anterior.")
        return {"message": "Pago ya procesado anteriormente",
            "data": {
                "Charge_Request_Id": existing_payment.Charge_Request_Id,
                "Equipo_Id": existing_payment.Equipo_Id,
                "Buy_Order": existing_payment.Buy_Order,
                "Charge": existing_payment.Charge,
                "Status": existing_payment.Status,
                "Token": existing_payment.Token,
            },
        }

    try:
        print(f"Ejecutando cobro de ${payload.Charge} para Equipo_Id: {payload.Equipo_Id}")
        transbank_response = await call_transbank(payload.Charge)
        new_payment = ChargeRequests(
            Equipo_Id=payload.Equipo_Id,
            Buy_Order=payload.Buy_Order,
            Idempotency_Key=key,
            Charge=payload.Charge,
            Status="COMPLETED",
            Token=transbank_response["token"],
        )
        session.add(new_payment)
        session.commit()
        session.refresh(new_payment)

        return {
            "status": "SUCCESS",
            "message": "Cobro exitoso",
            "data": {
                "Charge_Request_Id": new_payment.Charge_Request_Id,
                "Equipo_Id": new_payment.Equipo_Id,
                "Buy_Order": new_payment.Buy_Order,
                "Charge": new_payment.Charge,
                "Status": new_payment.Status,
                "Token": new_payment.Token,
            },
        }
    except Exception as e:
        session.rollback()
        print(f"Fallo al procesar el pago: {str(e)}")

        try:
            failed_payment = ChargeRequests(
                Equipo_Id=payload.Equipo_Id,
                Buy_Order=payload.Buy_Order,
                Idempotency_Key=key,
                Charge=payload.Charge,
                Status="FAILED",
                Token=None,
            )
            session.add(failed_payment)
            session.commit()
        except SQLAlchemyError as db_err:
            session.rollback()
            print(f"No se pudo guardar el estado FAILED: {str(db_err)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"status": "FAILED",
                    "message": "Error en pasarela externa", "error": str(e)},
        )


@router.post("/payments/refund")
async def refund_payment(payload: RefundRequest):
    try:
        print(
            f"Iniciando reembolso de ${payload.Charge} "f"para Equipo_Id: {payload.Equipo_Id} (Token: {payload.Token})"
        )

        await asyncio.sleep(0.5)
        refund_record = RefundRequests(
            Equipo_Id=payload.Equipo_Id,
            Token=payload.Token,
            Charge=payload.Charge,
            Status="REFUNDED",
        )

        session.add(refund_record)
        payment_to_refund = (
            session.query(ChargeRequests)
            .filter(ChargeRequests.Token == payload.Token)
            .first()
        )

        if payment_to_refund:
            payment_to_refund.Status = "REFUNDED"
        session.commit()
        session.refresh(refund_record)

        print(f"Reembolso aplicado exitosamente")
        return {
            "status": "REFUNDED",
            "message": f"Reembolso de ${payload.Charge} ejecutado correctamente.",
            "refund_id": refund_record.Refund_Request_Id,
        }
    except Exception as e:
        session.rollback()
        print(f"Falló el reembolso: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "REFUND_FAILED", "message": "El reembolso falló, requiere revisión."},
        )


async def call_transbank(amount: float):
    if os.getenv("SIMULATE_GATEWAY_LAG") == "true":
        await asyncio.sleep(6)

    if os.getenv("SIMULATE_GATEWAY_DOWN") == "true":
        raise Exception("Timeout: La pasarela Transbank no responde")

    return {
        "token": "TKN_PYTHON_WEB_SIMULATED_98765",
        "url": "https://webpay3gint.transbank.cl/webpayserver/initTransaction",
    }