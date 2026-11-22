from models import Base
from fastapi import FastAPI
from database import engine
from routes import router as payments_router

app = FastAPI(title="Pagos", version="1.0")
Base.metadata.create_all(bind=engine)
app.include_router(payments_router)

@app.get("/")
def start():
    return {"Servicio de Pagos funcionando"}

@app.get("/health")
def health():
    return {"Estado": "Activo"}