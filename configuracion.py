import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = "KOKOROKOOOO"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

URL_DATABASE = os.getenv("URL_DATABASE")

if not URL_DATABASE:
    raise ValueError("URL_DATABASE no está configurado")

ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://localhost:3000", 
    "https://imperium-sound-frontend-olby.vercel.app",
    "https://imperium-sound-backend.vercel.app",
    "http://localhost:8000"
]

ALLOWED_AUDIO_TYPES = ["audio/webm", "audio/wav", "audio/mp3", "audio/mpeg", "audio/ogg"]
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB