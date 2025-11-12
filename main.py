from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from configuracion import ORIGINS
from routes import autenticacion_routes, user_routes, sound_routes, admin_routes

app = FastAPI(
    title="Imperium Sound API",
    description="API para gestión de sonidos y usuarios",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.include_router(autenticacion_routes.router)
app.include_router(user_routes.router)
app.include_router(sound_routes.router)
app.include_router(admin_routes.router)

@app.get("/")
async def root():
    return {"message": "Bienvenido a Imperium Sound API"}