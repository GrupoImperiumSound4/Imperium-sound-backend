from fastapi import APIRouter, Depends
from database import SessionDepends
from services.autenticacion_service import AuthService
from utils.dependencias import get_current_user_dependency

router = APIRouter(prefix="/user", tags=["Users"])

@router.get("/me")
async def get_current_user(
    db: SessionDepends,
    current_user: dict = Depends(get_current_user_dependency)
):
    return AuthService.get_current_user(db, current_user.get("user_id"))

@router.get("/valid")
async def validate_token(current_user: dict = Depends(get_current_user_dependency)):
    return current_user