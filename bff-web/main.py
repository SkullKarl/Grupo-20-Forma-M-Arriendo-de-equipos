
import os
import asyncio
import time
import httpx

from fastapi import FastAPI, HTTPException


app = FastAPI(
    title="BFF Web - Arriendo de Equipos",
    description="Backend for Frontend de la plataforma de arriendo",
    version="1.2.0"
)

AVAILABILITY_URL = os.getenv(
    "AVAILABILITY_URL",
    "http://localhost:8001"
)

DELIVERY_URL = os.getenv(
    "DELIVERY_URL",
    "http://localhost:8003"
)


MAX_FALLOS = 3
TIEMPO_RECUPERACION = 15
MAX_CONSULTAS_SIMULTANEAS = 5
TIEMPO_ESPERA_BULKHEAD = 0.1


class CircuitoAbierto(Exception):
    """Se lanza cuando el Circuit Breaker impide una consulta."""
    pass


class BulkheadSaturado(Exception):
    """Se lanza cuando no se puede adquirir un espacio disponible."""
    pass


class CircuitBreaker:
    def __init__(self, max_fallos=3, tiempo_recuperacion=15):
        self.max_fallos = max_fallos
        self.tiempo_recuperacion = tiempo_recuperacion
        self.fallos = 0
        self.estado = "CLOSED"
        self.momento_apertura = 0
        self.prueba_en_curso = False

    def permitir_peticion(self):
        if self.estado == "OPEN":
            tiempo_transcurrido = time.monotonic() - self.momento_apertura

            if tiempo_transcurrido < self.tiempo_recuperacion:
                raise CircuitoAbierto(
                    "Circuit Breaker abierto: servicio temporalmente bloqueado."
                )

            self.estado = "HALF_OPEN"
            self.prueba_en_curso = False

        if self.estado == "HALF_OPEN":
            if self.prueba_en_curso:
                raise CircuitoAbierto(
                    "Circuit Breaker en recuperación: prueba en curso."
                )

            self.prueba_en_curso = True

    def registrar_exito(self):
        self.fallos = 0
        self.estado = "CLOSED"
        self.prueba_en_curso = False

    def registrar_fallo(self):
        self.fallos += 1
        self.prueba_en_curso = False

        if self.estado == "HALF_OPEN" or self.fallos >= self.max_fallos:
            self.estado = "OPEN"
            self.momento_apertura = time.monotonic()


# Un Circuit Breaker independiente para cada servicio.
circuitos = {
    "Disponibilidad": CircuitBreaker(MAX_FALLOS, TIEMPO_RECUPERACION),
    "Entregas": CircuitBreaker(MAX_FALLOS, TIEMPO_RECUPERACION)
}

# Un Bulkhead independiente para cada servicio.
bulkheads = {
    "Disponibilidad": asyncio.Semaphore(MAX_CONSULTAS_SIMULTANEAS),
    "Entregas": asyncio.Semaphore(MAX_CONSULTAS_SIMULTANEAS)
}



async def solicitar_servicio(base_url, endpoint, nombre):
    circuito = circuitos[nombre]
    bulkhead = bulkheads[nombre]

    circuito.permitir_peticion()

    try:
        # Intentamos conseguir un espacio en el Bulkhead.
        try:
            await asyncio.wait_for(
                bulkhead.acquire(),
                timeout=TIEMPO_ESPERA_BULKHEAD
            )
        except asyncio.TimeoutError:
            raise BulkheadSaturado(
                f"El servicio {nombre} alcanzó su límite "
                "de consultas simultáneas."
            )

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{base_url}{endpoint}"
                )

                response.raise_for_status()
                resultado = response.json()

        finally:
            # Siempre liberamos el espacio ocupado.
            bulkhead.release()

        circuito.registrar_exito()
        return resultado

    except BulkheadSaturado:
        # La saturación no significa que el microservicio falló.
        # Tampoco debemos dejar bloqueada una prueba HALF_OPEN.
        if circuito.estado == "HALF_OPEN":
            circuito.prueba_en_curso = False

        raise

    except Exception:
        circuito.registrar_fallo()
        raise



async def consultar_servicio(base_url, endpoint, nombre):
    try:
        resultado = await solicitar_servicio(
            base_url,
            endpoint,
            nombre
        )
        return resultado, None

    except CircuitoAbierto:
        return None, (
            f"El servicio {nombre} está temporalmente bloqueado "
            "por el Circuit Breaker."
        )

    except httpx.TimeoutException:
        return None, f"El servicio {nombre} demoró demasiado."

    except httpx.HTTPStatusError:
        return None, f"El servicio {nombre} respondió con un error."

    except httpx.RequestError:
        return None, f"No fue posible conectar con {nombre}."

    except BulkheadSaturado as error:
        return None, str(error)

    except Exception:
        return None, f"Error inesperado al consultar {nombre}."


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "bff-web"
    }


@app.get("/web/dashboard")
async def web_dashboard():

    resultados = await asyncio.gather(
        consultar_servicio(
            AVAILABILITY_URL,
            "/equipments",
            "Disponibilidad"
        ),
        consultar_servicio(
            AVAILABILITY_URL,
            "/reservations",
            "Disponibilidad"
        ),
        consultar_servicio(
            DELIVERY_URL,
            "/deliveries",
            "Entregas"
        )
    )

    equipos, error_equipos = resultados[0]
    reservas, error_reservas = resultados[1]
    entregas, error_entregas = resultados[2]

    equipos = equipos if equipos is not None else []
    reservas = reservas if reservas is not None else []

    if entregas is None:
        entregas = {"value": [], "Count": 0}

    errores = {}

    if error_equipos:
        errores["equipos"] = error_equipos

    if error_reservas:
        errores["reservas"] = error_reservas

    if error_entregas:
        errores["entregas"] = error_entregas

    total_entregas = (
        entregas.get("Count", len(entregas.get("value", [])))
        if isinstance(entregas, dict)
        else len(entregas) if isinstance(entregas, list) else 0
    )

    return {
        "estado": "parcial" if errores else "correcto",
        "equipos": equipos,
        "reservas": reservas,
        "entregas": entregas,
        "resumen": {
            "total_equipos": len(equipos),
            "total_reservas": len(reservas),
            "total_entregas": total_entregas
        },
        "errores": errores
    }


@app.get("/web/equipments")
async def web_equipments():
    try:
        return await solicitar_servicio(
            AVAILABILITY_URL,
            "/equipments",
            "Disponibilidad"
        )

    except CircuitoAbierto as error:
        raise HTTPException(status_code=503, detail=str(error))

    except BulkheadSaturado as error:
        raise HTTPException(status_code=503, detail=str(error))

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="El servicio de Disponibilidad demoró demasiado"
        )

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=502,
            detail="El servicio de Disponibilidad respondió con un error"
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="No fue posible conectar con Disponibilidad"
        )


@app.get("/web/deliveries")
async def web_deliveries():
    try:
        return await solicitar_servicio(
            DELIVERY_URL,
            "/deliveries",
            "Entregas"
        )

    except CircuitoAbierto as error:
        raise HTTPException(status_code=503, detail=str(error))

    except BulkheadSaturado as error:
        raise HTTPException(status_code=503, detail=str(error))

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="El servicio de Entregas demoró demasiado"
        )

    except httpx.HTTPStatusError:
        raise HTTPException(
            status_code=502,
            detail="El servicio de Entregas respondió con un error"
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="No fue posible conectar con Entregas"
        )
