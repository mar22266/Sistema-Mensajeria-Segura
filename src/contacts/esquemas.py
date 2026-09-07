from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# clase de esquema para crear un contacto
class CrearContactoEntrada(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    email: EmailStr


# clase de esquema para actualizar un contacto
class ActualizarContactoEntrada(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    email: EmailStr


# clase de esquema para la salida de un contacto
class ContactoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ownerId: UUID
    nombre: str
    email: EmailStr
    createdAt: datetime
