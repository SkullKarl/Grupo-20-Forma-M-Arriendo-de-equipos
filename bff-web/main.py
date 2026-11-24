import httpx
import os

from fastapi import FastAPI, HTTPException

app = FastAPI(
    title = "BFF Web - Arriendo de Equipos",
    description = "Backend for Frontend de la plataforma de arriendo",
    version = "1.0.0"
)

AVAILABILITY_URL = os.getenv(
    "AVAILABILITY_URL",
    "http://localhost:8001"
)

async def consultar_disponibilidad(client, endpoint):
    try:
        response = await client.get(
            f"{AVAILABILITY_URL}{endpoint}"
        )
        response.raise_for_status()

        return response.json(), None

    except httpx.TimeoutException:
        return None, "El servicio demoró demasiado."

    except httpx.HTTPStatusError:
        return None, "El servicio respondió con un error."

    except httpx.RequestError:
        return None, "No fue posible conectar con Disponibilidad."

@app.get("/health")
def health():
    return {"status": "ok", "service": "bff-web"}

@app.get("/web/dashboard")
async def web_dashboard():

    async with httpx.AsyncClient(timeout=5.0) as client:

        equipos, error_equipos = await consultar_disponibilidad(
            client, "/equipments"
        )

        reservas, error_reservas = await consultar_disponibilidad(
            client, "/reservations"
        )

    # Si un servicio falla, conservamos una respuesta utilizable.
    equipos = equipos if equipos is not None else []
    reservas = reservas if reservas is not None else []

    errores = {}

    if error_equipos:
        errores["equipos"] = error_equipos

    if error_reservas:
        errores["reservas"] = error_reservas

    return {
        "estado": "parcial" if errores else "correcto",
        "equipos": equipos,
        "reservas": reservas,
        "resumen": {
            "total_equipos": len(equipos),
            "total_reservas": len(reservas)
        },
        "errores": errores
    }

@app.get("/web/equipments")
async def web_equipments():

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{AVAILABILITY_URL}/equipments"
            )

        response.raise_for_status()

        return response.json()

    except httpx.TimeoutException:
        raise HTTPException(
            status_code = 504,
            detail = "El servicio de Disponibilidad demoró demasiado"
        )

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code = 502,
            detail = "El servicio de Disponibilidad respondió con un error"
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code = 503,
            detail = "No fue posible conectar con Disponibilidad"
        )