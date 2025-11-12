from fastapi import APIRouter, Response
from database import SessionDepends
from models.esquemas import Registro, Login
from services.autenticacion_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/registro")
def crear_usuario(db: SessionDepends, data: Registro):
    return AuthService.crear_usuario(db, data)

@router.post("/login")
async def login_user(data: Login, db: SessionDepends, response: Response):
    result = AuthService.login_user(db, data)
    
    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        httponly=True,
        secure=True,       # False para localhost, True para HTTPS
        samesite="lax",
        max_age=604800,
        path="/",
    )

    
    return result

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        path="/",
        domain=None
    )    
    return {"message": "Sesión cerrada exitosamente"}