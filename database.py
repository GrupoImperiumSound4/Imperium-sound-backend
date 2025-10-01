from typing import Annotated
from fastapi import Depends
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

import os
from dotenv import load_dotenv

load_dotenv()
URL_DATABASE = os.getenv("URL_DATABASE")

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
