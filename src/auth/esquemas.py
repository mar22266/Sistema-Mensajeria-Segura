from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# clase de esquemas para la validacion de datos de entrada y salida de la API
# registro de usuario
class RegistroUsuarioEntrada(BaseModel):
    displayName: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


# clase para la salida de datos del registro de usuario
class RegistroUsuarioSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    displayName: str
    createdAt: datetime


# clase para la salida de datos del estado del servicio
class EstadoServicioSalida(BaseModel):
    estado: str
    servicio: str
    version: str


# clase para la entrada de datos del login de usuario
class LoginUsuarioEntrada(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


# clase para la salida de datos del login de usuario
class LoginUsuarioSalida(BaseModel):
    accessToken: str
    tokenType: str
    userId: UUID
    email: EmailStr
    displayName: str
