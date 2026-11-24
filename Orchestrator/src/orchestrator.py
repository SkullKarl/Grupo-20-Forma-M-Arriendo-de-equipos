import os
import httpx

AVAILABILITY_URL = os.getenv("AVAILABILITY_SERVICE_URL", "http://service-disponibilidad:8000")
PAYMENTS_URL = os.getenv("PAYMENTS_SERVICE_URL", "http://service-pagos:8000")
DELIVERY_URL = os.getenv("DELIVERY_SERVICE_URL", "http://service-entrega:8000")

async def run_rental_saga(payload) -> dict:
    steps = []
    reserved = False
    charged = False
    payment_token = None
    idem_key = payload.Idempotency_Key or payload.Buy_Order

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res_avail = await client.post(
                f"{AVAILABILITY_URL}/availability/reserve",
                json={
                    "rental_id": payload.Rental_Id,
                    "equipment_id": payload.Equipo_Id,
                    "start_date": payload.Start_Date,
                    "end_date": payload.End_Date,
                },
            )
            res_avail.raise_for_status()
            reserved = True
            steps.append({"step": "availability_reserve", "status": "COMPLETED", "detail": res_avail.json()})
        except Exception as e:
            steps.append({"step": "availability_reserve", "status": "FAILED", "detail": {"error": str(e)}})
            return {
                "saga_status": "FAILED",
                "message": "No se pudo reservar la disponibilidad del equipo.",
                "rental_id": payload.Rental_Id,
                "payment_token": None,
                "steps": steps,
            }

        try:
            res_pay = await client.post(
                f"{PAYMENTS_URL}/payments/charge",
                headers={"Idempotency-Key": idem_key},
                json={
                    "Equipo_Id": payload.Equipo_Id,
                    "Buy_Order": payload.Buy_Order,
                    "Session_Id": payload.Session_Id,
                    "Charge": payload.Charge,
                },
            )
            res_pay.raise_for_status()
            pay_body = res_pay.json()
            payment_token = (pay_body.get("data") or {}).get("Token")
            charged = True
            steps.append({"step": "payments_charge", "status": "COMPLETED", "detail": pay_body})
        except Exception as e:
            steps.append({"step": "payments_charge", "status": "FAILED", "detail": {"error": str(e)}})
            await _compensate_availability(client, payload, steps)
            return {
                "saga_status": "COMPENSATED",
                "message": "Falló el cobro; se revirtió la reserva de disponibilidad.",
                "rental_id": payload.Rental_Id,
                "payment_token": None,
                "steps": steps,
            }

        try:
            res_del = await client.post(
                f"{DELIVERY_URL}/deliveries/schedule",
                json={
                    "Equipment_Id": payload.Equipo_Id,
                    "Delivery_Date": payload.Delivery_Date,
                },
            )
            res_del.raise_for_status()
            steps.append({"step": "delivery_schedule", "status": "COMPLETED", "detail": res_del.json()})
            return {
                "saga_status": "COMPLETED",
                "message": "Orden completada: equipo reservado, pagado y entrega agendada.",
                "rental_id": payload.Rental_Id,
                "payment_token": payment_token,
                "steps": steps,
            }
        except Exception as e:
            steps.append({"step": "delivery_schedule", "status": "FAILED", "detail": {"error": str(e)}})
            if charged and payment_token:
                await _compensate_refund(client, payload, payment_token, steps)
            if reserved:
                await _compensate_availability(client, payload, steps)
            return {
                "saga_status": "COMPENSATED",
                "message": "Falló el agendado de la entrega; se ejecutaron las compensaciones.",
                "rental_id": payload.Rental_Id,
                "payment_token": payment_token,
                "steps": steps,
            }


async def _compensate_refund(client: httpx.AsyncClient, payload, payment_token: str, steps: list):
    try:
        res_ref = await client.post(
            f"{PAYMENTS_URL}/payments/refund",
            json={
                "Equipo_Id": payload.Equipo_Id,
                "Charge": payload.Charge,
                "Token": payment_token,
            },
        )
        res_ref.raise_for_status()
        steps.append({"step": "compensate_refund", "status": "COMPLETED", "detail": res_ref.json()})
    except Exception as e:
        steps.append({"step": "compensate_refund", "status": "FAILED", "detail": {"error": str(e)}})


async def _compensate_availability(client: httpx.AsyncClient, payload, steps: list):
    try:
        res_rel = await client.post(
            f"{AVAILABILITY_URL}/availability/release",
            json={
                "rental_id": payload.Rental_Id,
                "equipment_id": payload.Equipo_Id,
            },
        )
        res_rel.raise_for_status()
        steps.append({"step": "compensate_availability", "status": "COMPLETED", "detail": res_rel.json()})
    except Exception as e:
        steps.append({"step": "compensate_availability", "status": "FAILED", "detail": {"error": str(e)}})