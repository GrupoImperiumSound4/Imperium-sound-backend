from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from database import SessionDepends
from sqlalchemy import text


app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://localhost:3000", 
    "https://imperium-sound-frontend-olby.vercel.app", 
    "http://localhost:8000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Registro(BaseModel):
    name: str
    email: str
    password: str

class Login(BaseModel):
    email: str 
    password: str

@app.get("/")
async def root(request: Request):
    return {"message": "Bienvenido"}

@app.post("/crear_usuario")
def crear_usuario(db: SessionDepends, data: Registro):
    try:
        db.execute(
            text("INSERT INTO users (name, email, password) VALUES (:name, :email, :password)"),
            {"name": data.name, "email": data.email, "password": data.password}
        )
        db.commit()
        return {"message": "usuario creado con exito"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al crear usuario: {str(e)}")

@app.post("/login")
async def login_user(data: Login, db: SessionDepends):
    try:
        consulta = db.execute(
            text("SELECT * FROM users WHERE email = :email"), 
            {"email": data.email}
        ).fetchone()

        if not consulta or consulta.password != data.password:
            raise HTTPException(status_code=400, detail="Credenciales inválidas")

        return {"message": f"Bienvenido {consulta.name}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error del servidor: {str(e)}")