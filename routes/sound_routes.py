from fastapi import APIRouter, File, UploadFile, Form
from database import SessionDepends
from services.sound_service import SoundService

router = APIRouter(prefix="/sounds", tags=["Sounds"])

@router.get("/puntos")
async def obtener_puntos(db: SessionDepends):
    return SoundService.obtener_puntos(db)

@router.post("/registro")
async def crear_audio(
    db: SessionDepends,
    audio: UploadFile = File(...),
    decibels: float = Form(...),
    id_point: int = Form(...)
):
    return await SoundService.crear_audio(db, audio, decibels, id_point)