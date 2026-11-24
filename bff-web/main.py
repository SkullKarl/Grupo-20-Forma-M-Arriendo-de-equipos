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

@app.get("/health")
def health():
    return {"status": "ok", "service": "bff-web"}

@app.get("/web/dashboard")
def dashboard():
    return {
        "equipos": [],
        "reservas": [],
        "entregas": [],
        "resumen": {
            "cantidad_equipos": 0,
            "cantidas_reservas": 0,
            "cantidad_entregas": 0
        }
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