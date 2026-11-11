from fastapi import FastAPI

from app.database import Base, engine
from app import models
from app.routes import router as disponibilidad_router

app = FastAPI(
    title = "Servicio Disponibilidad",
    description = "Administración de equipos y reservas",
    version = "1.0.0"
)

# Crear tablas de base de datos, si todavía no existen
Base.metadata.create_all(bind=engine)

# rutas de Disponibildad
app.include_router(disponibilidad_router)

@app.get("/")
def inicio():
    return {
        "mensaje": "Servicio de Disponibilidad funcionando"
    }

@app.get("/health")
def health():
    return{
        "estado": "activo"
    }