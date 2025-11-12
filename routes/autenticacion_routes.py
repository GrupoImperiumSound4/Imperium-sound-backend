from fastapi import APIRouter, Response, Request, HTTPException
from database import SessionDepends
from models.esquemas import Registro, Login
from services.autenticacion_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/registro")
def crear_usuario(db: SessionDepends, data: Registro):
    return AuthService.crear_usuario(db, data)

@router.post("/login")
async def login_user(data: Login, db: SessionDepends, response: Response, request: Request):
    result = AuthService.login_user(db, data)
    
    # Detectar si es producción (Vercel) o desarrollo (localhost)
    is_production = "vercel.app" in str(request.url) or "vercel.app" in request.headers.get("origin", "")
    
    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        httponly=True,
        secure=is_production,  # True en HTTPS
        samesite="none" if is_production else "lax",
        max_age=604800,  # 7 días
        path="/",
        domain=None
    )
    
    return {
        "token_type": "bearer",
        "user": result["user"]
    }

@router.get("/me")
async def get_current_user_info(request: Request, db: SessionDepends):
    """Endpoint para validar el token y obtener info del usuario"""
    token = AuthService.get_token_from_request(request)
    
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    payload = AuthService.verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    
    return AuthService.get_current_user(db, payload["user_id"])

@router.post("/logout")
async def logout(response: Response, request: Request):
    is_production = "vercel.app" in str(request.url) or "vercel.app" in request.headers.get("origin", "")
    
    response.set_cookie(
        key="access_token",
        value="",
        httponly=True,
        secure=is_production,
        samesite="none" if is_production else "lax",
        max_age=0,  
        path="/",
        domain=None
    )
 
    return {"message": "Sesión cerrada exitosamente"}