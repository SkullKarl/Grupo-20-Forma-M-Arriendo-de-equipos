from fastapi import APIRouter
from orchestrator import run_rental_saga
from schemas import RentalSagaRequest, RentalSagaResponse

router = APIRouter()

@router.post("/sagas/rentals", response_model=RentalSagaResponse)
async def start_rental_saga(payload: RentalSagaRequest):
    return await run_rental_saga(payload)