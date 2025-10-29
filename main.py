# main.py
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import SessionDepends
from sqlalchemy import text
import jwt
from datetime import datetime, timedelta
from typing import Optional

# ================= CONFIGURACIÓN =================
SECRET_KEY = "KOKOROKOOOO"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

app = FastAPI()

# Orígenes permitidos (ajusta según tu dominio real)
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://imperium-sound-frontend-olby.vercel.app",  # TU FRONTEND
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,   # Necesario para cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= MODELOS =================
class Login(BaseModel):
    email: str
    password: str

# ================= JWT =================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None

def get_token_from_request(request: Request) -> Optional[str]:
    token = request.cookies.get("access_token")
    if token:
        return token
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        return auth.split(" ")[1]
    return None

# ================= RUTAS =================
@app.post("/login")
async def login_user(data: Login, db: SessionDepends, response: Response):
    try:
        user = db.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {"email": data.email}
        ).fetchone()

        if not user or user.password != data.password:
            raise HTTPException(status_code=400, detail="Credenciales inválidas")

        token_data = {
            "user_id": user.id,
            "email": user.email,
            "name": user.name
        }
        token = create_access_token(token_data)

        # Cookie segura para producción
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=7 * 24 * 60 * 60,
            path="/",
            domain=".vercel.app"  # ← ESTO PERMITE SUBDOMINIOS
        )

        return {
            "message": f"Bienvenido {user.name}",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error del servidor: {str(e)}")

# Ruta protegida de ejemplo
@app.get("/me")
async def get_current_user(request: Request, db: SessionDepends):
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")

    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    user = db.execute(
        text("SELECT id, name, email FROM users WHERE id = :user_id"),
        {"user_id": payload["user_id"]}
    ).fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {"id": user.id, "name": user.name, "email": user.email}