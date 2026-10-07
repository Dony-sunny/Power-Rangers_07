from fastapi import APIRouter, Depends, HTTPException
from backend.auth import get_actor
from backend.services import public_context

router = APIRouter(prefix="/api/corridor-context", tags=["public reference context"])


@router.get("")
def corridor(actor=Depends(get_actor)):
    return public_context.corridor_context()


@router.get("/weather")
def weather(location: str = "maradu", actor=Depends(get_actor)):
    if location not in public_context.LOCATIONS:
        raise HTTPException(422, "Select a supported corridor location.")
    return public_context.weather(location)
