from fastapi import FastAPI
from routes import router as saga_router

app = FastAPI(title="Orquestador Saga", version="1.0")
app.include_router(saga_router)

@app.get("/")
def start():
    return {"Servicio de Orquestación Saga funcionando"}

@app.get("/health")
def health():
    return {"Estado": "Activo"}