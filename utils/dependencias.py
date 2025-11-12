from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from services.autenticacion_service import AuthService

def get_current_user_dependency(request: Request, db: Session = Depends(get_db)):
    """Dependencia para obtener el usuario actual desde el token"""
    token = AuthService.get_token_from_request(request)
    
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    payload = AuthService.verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    
    return payload