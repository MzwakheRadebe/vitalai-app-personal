"""Staff routes — doctor directory for appointment booking."""

from fastapi import APIRouter
from app.doctors import DOCTORS

router = APIRouter(prefix="/staff")


@router.get("/doctors")
async def list_doctors():
    """
    Return the list of available doctors.
    Public — no auth required so the booking form can show the picker
    before a patient is signed in.
    """
    return [
        {"email": d["email"], "name": d["name"], "department": d["department"]}
        for d in DOCTORS
    ]
