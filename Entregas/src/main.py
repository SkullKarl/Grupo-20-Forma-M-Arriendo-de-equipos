from models import Base
from fastapi import FastAPI
from database import engine
from routes import router as deliveries_router

app = FastAPI(title="Entregas", version="1.0")
Base.metadata.create_all(bind=engine)
app.include_router(deliveries_router)

@app.get("/")
def start():
    return {"Servicio de Entrega funcionando"}

@app.get("/health")
def health():
    return {"Estado": "Activo"}