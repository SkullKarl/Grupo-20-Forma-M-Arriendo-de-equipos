import os
import time
import secrets
from collections import defaultdict, deque

import httpx
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import Response


# Configuración
BFF_URL = os.getenv("BFF_URL", "http://bff-web:8000")
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://service-orquestador:8000")
AVAILABILITY_URL = os.getenv("AVAILABILITY_URL", "http://service-disponibilidad:8000")
GATEWAY_API_TOKEN = os.getenv("GATEWAY_API_TOKEN")

# Rate Limiting: máximo de solicitudes por IP
RATE_LIMIT = 60
RATE_WINDOW = 60  # segundos

solicitudes = defaultdict(deque)


app = FastAPI(
    title="API Gateway",
    description="Punto de entrada para los servicios del sistema de arriendo",
    version="1.0.0"
)


# Comprobación de salud: ruta pública
@app.get("/health")
def health():
    return {"estado": "activo", "servicio": "API Gateway"}


# Autenticación mediante Bearer Token
async def validar_token(
    authorization: str = Header(default=None)
):
    if not GATEWAY_API_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="El token del Gateway no está configurado."
        )

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Falta el token de autenticación."
        )

    esquema, separador, token = authorization.partition(" ")

    if (
        esquema.lower() != "bearer"
        or not separador
        or not secrets.compare_digest(token, GATEWAY_API_TOKEN)
    ):
        raise HTTPException(
            status_code=401,
            detail="Token inválido."
        )


# Limitación de solicitudes por dirección IP
async def verificar_rate_limit(request: Request):
    ip = request.client.host if request.client else "desconocida"
    ahora = time.monotonic()

    historial = solicitudes[ip]

    while historial and ahora - historial[0] >= RATE_WINDOW:
        historial.popleft()

    if len(historial) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Demasiadas solicitudes. Intenta nuevamente más tarde."
        )

    historial.append(ahora)


# Función reutilizable de proxy hacia microservicios internos
async def _reenviar(request: Request, destino: str, nombre_servicio: str, authorization: str | None):
    await validar_token(authorization)
    await verificar_rate_limit(request)

    encabezados = {
        nombre: valor
        for nombre, valor in request.headers.items()
        if nombre.lower() not in {
            "host",
            "content-length",
            "connection",
            "authorization",
            "transfer-encoding"
        }
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            respuesta = await client.request(
                method=request.method,
                url=destino,
                params=request.query_params,
                content=await request.body(),
                headers=encabezados
            )

        encabezados_respuesta = {
            nombre: valor
            for nombre, valor in respuesta.headers.items()
            if nombre.lower() not in {
                "content-length",
                "content-encoding",
                "transfer-encoding",
                "connection"
            }
        }

        return Response(
            content=respuesta.content,
            status_code=respuesta.status_code,
            headers=encabezados_respuesta
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail=f"No fue posible comunicarse con {nombre_servicio}."
        )


# Reenviar solicitudes al BFF
@app.api_route("/web", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@app.api_route("/web/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def redirigir_bff(request: Request, path: str = "", authorization: str = Header(default=None)):
    destino = f"{BFF_URL}/web/{path}" if path else f"{BFF_URL}/web"
    return await _reenviar(request, destino, "el BFF", authorization)


# Reenviar solicitudes al Orquestador Saga
@app.api_route("/sagas/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def redirigir_orquestador(request: Request, path: str, authorization: str = Header(default=None)):
    destino = f"{ORCHESTRATOR_URL}/sagas/{path}"
    return await _reenviar(request, destino, "el Orquestador", authorization)


# Reenviar gestión de equipos a Disponibilidad
@app.api_route("/equipments", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@app.api_route("/equipments/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def redirigir_disponibilidad(request: Request, path: str = "", authorization: str = Header(default=None)):
    destino = f"{AVAILABILITY_URL}/equipments/{path}" if path else f"{AVAILABILITY_URL}/equipments"
    return await _reenviar(request, destino, "Disponibilidad", authorization)