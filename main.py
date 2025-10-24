from fastapi import FastAPI, Request, HTTPException, File, UploadFile, Form, Response
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from database import SessionDepends
from sqlalchemy import text
import jwt
from typing import Optional

SECRET_KEY = "KOKOROKOOOO"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

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

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None



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
async def login_user(data: Login, db: SessionDepends, respone: Response):
    try:
        consulta = db.execute(
            text("SELECT * FROM users WHERE email = :email"), 
            {"email": data.email}
        ).fetchone()

        if not consulta or consulta.password != data.password:
            raise HTTPException(status_code=400, detail="Credenciales inválidas")
        
        token_data = {
            "user_id": consulta.id,
            "email": consulta.email,
            "name": consulta.name
        }
        token = create_access_token(data=token_data)


        respone.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=604800,
        )

        return {"message": f"Bienvenido {consulta.name}",
                "user": {
                    "id": consulta.id,
                    "name": consulta.name,
                    "email":consulta.email
                }
                }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error del servidor: {str(e)}")
    
#--------------Token-----------------------------

@app.get("/valid")
async def validate_token(request: Request):
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    return payload

@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Sesión cerrada exitosamente"}

@app.get("/me")
async def get_current_user(request: Request, db: SessionDepends):
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    
    try:
        user = db.execute(
            text("SELECT id, name, email FROM users WHERE id = :user_id"),
            {"user_id": payload.get("user_id")}
        ).fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener datos del usuario: {str(e)}")
#-------------sonidos-----------------

@app.get("/puntos")
async def obt_sonidos(db: SessionDepends):
    try:
        consulta = db.execute(text("SELECT * FROM point ORDER BY floor, area")).fetchall()

        puntos = [
            {
                "id": columna.id,
                "floor": columna.floor,
                "area": columna.area
            }
            for columna in consulta
        ]
        return{
            "puntos": puntos,
            "cuenta": len(puntos)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"error al obtener los puntos: {str(e)}")

@app.post("/Registro-sonido")
async def crear_audio(db: SessionDepends, audio: UploadFile = File(...), decibels: float = Form(...), id_point: int = Form(...)):
    try:
        tipos = ["audio/webm", "audio/wav", "audio/mp3", "audio/mpeg", "audio/ogg"]
        if audio.content_type not in tipos:
            raise HTTPException(status_code=400, detail="tipo de archivo no permitido")
        #leer el audio
        audio_data = await audio.read()
        Tamaño_archivo = len(audio_data)
        #tamaño maximo del audio: 20Mb
        Tamaño_maximo = 20 * 1024 * 1024

        if Tamaño_archivo > Tamaño_maximo:
            raise HTTPException(status_code=400, detail="Mano ese archivo es muuuy grande. Maximo 20Mb")
        
            verificar_punto = db.execute(text("SELECT id FROM point  WHERE id = :id "), {"id": id_point})

        consulta = db.execute(text("INSERT INTO sounds (sound, decibels, date, id_point) VALUES (:sound, :decibels, :date, :id_point) RETURNING id, date"),
                              {"sound": audio_data,
                               "decibels": decibels,
                               "date": datetime.utcnow(),
                               "id_point": id_point
                               }
                              )

        db.commit()
        insertado = consulta.fetchone()

        return {
            "mesagge": "Audio guardado como era",  "id": insertado.id,  "decibels": decibels,   "id_point": id_point,
            "Tamaño_archivo": Tamaño_archivo,   "content_type": audio.content_type,   "date": insertado.date.isoformat()
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"error al guardar el audio {str(e)}")
