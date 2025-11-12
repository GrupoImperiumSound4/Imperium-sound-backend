from datetime import datetime, timedelta
from fastapi import HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
import jwt
from configuracion import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_DAYS
from models.esquemas import Registro, Login

class AuthService:
    @staticmethod
    def crear_usuario(db: Session, data: Registro):
        try:
            # Verificar si el usuario ya existe
            existe = db.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": data.email}
            ).fetchone()

            if existe:
                raise HTTPException(status_code=400, detail="El email ya está registrado")

            # Insertar usuario
            result = db.execute(
                text("INSERT INTO users (name, email, password, role) VALUES (:name, :email, :password, 'user') RETURNING id"),
                {"name": data.name, "email": data.email, "password": data.password}
            )
            db.commit()
            
            user_id = result.fetchone().id

            return {
                "message": "Usuario creado exitosamente",
                "user_id": user_id
            }
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error al crear usuario: {str(e)}")

    @staticmethod
    def login_user(db: Session, data: Login):
        try:
            # Buscar usuario con su rol
            user = db.execute(
                text("SELECT id, name, email, password, role FROM users WHERE email = :email"),
                {"email": data.email}
            ).fetchone()

            if not user or user.password != data.password:
                raise HTTPException(status_code=401, detail="Credenciales incorrectas")

            # Crear token JWT incluyendo el rol
            token_data = {
                "user_id": user.id,
                "email": user.email,
                "role": user.role,  # Incluir rol en el token
                "exp": datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
            }
            
            access_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role
                }
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al iniciar sesión: {str(e)}")

    @staticmethod
    def get_current_user(db: Session, user_id: int):
        try:
            user = db.execute(
                text("SELECT id, name, email, role FROM users WHERE id = :id"),
                {"id": user_id}
            ).fetchone()

            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

            return {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al obtener usuario: {str(e)}")

    @staticmethod
    def get_token_from_request(request: Request) -> str:
        """Extraer el token desde las cookies de la petición"""
        token = request.cookies.get("access_token")
        return token

    @staticmethod
    def verify_token(token: str):
        """Verificar y decodificar el token JWT"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None