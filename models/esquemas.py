from pydantic import BaseModel, EmailStr

class Registro(BaseModel):
    name: str
    email: EmailStr
    password: str

class Login(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

class PuntoResponse(BaseModel):
    id: int
    floor: int
    area: str