
from sqlalchemy import inspect, text
from fastapi import FastAPI

from app.database import Base, engine
from app import models
from app.routes import router as disponibilidad_router

app = FastAPI(
    title="Servicio Disponibilidad",
    description="Administración de equipos y reservas",
    version="1.1.0"
)

# Crear las tablas que todavía no existan.
Base.metadata.create_all(bind=engine)

# Agregar rental_id a instalaciones que ya tenían reservas.
columnas = [
    columna["name"]
    for columna in inspect(engine).get_columns("reservations")
]

if "rental_id" not in columnas:
    with engine.begin() as conexion:
        conexion.execute(
            text("ALTER TABLE reservations ADD COLUMN rental_id VARCHAR")
        )

# Corregir el error histórico de escritura en el estado.
with engine.begin() as conexion:
    conexion.execute(
        text(
            "UPDATE reservations "
            "SET status = 'reserved' "
            "WHERE status = 'reserverd'"
        )
    )

app.include_router(disponibilidad_router)


@app.get("/")
def inicio():
    return {
        "mensaje": "Servicio de Disponibilidad funcionando"
    }


@app.get("/health")
def health():
    return {
        "estado": "activo"
    }
