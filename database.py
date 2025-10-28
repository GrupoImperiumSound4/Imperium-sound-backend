from typing import Annotated
from fastapi import Depends
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

import os
from dotenv import load_dotenv

load_dotenv()
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")
URL_DATABASE = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

if not URL_DATABASE:
    raise ValueError(
        "URL_DATABASE no está configurado"
    )
if URL_DATABASE:
    print("ESO fueee")

engine = create_engine(URL_DATABASE)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    with SessionLocal() as session:
        yield session

SessionDepends = Annotated[Session, Depends(get_db)]
