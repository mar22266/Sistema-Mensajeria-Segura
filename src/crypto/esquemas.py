from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CrearGrupoEntrada(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    creadoPor: UUID
    miembrosIds: list[UUID] = Field(min_length=1)


class CrearGrupoSalida(BaseModel):
    groupId: UUID
    nombre: str
    creadoPor: UUID
    miembrosIds: list[UUID]
    createdAt: datetime


class EnviarMensajeEntrada(BaseModel):
    senderId: UUID
    plaintext: str = Field(min_length=1)


class EnviarMensajeSalida(BaseModel):
    messageId: UUID
    senderId: UUID
    recipientId: UUID | None
    groupId: UUID | None
    ciphertext: str
    encryptedKey: str
    nonce: str
    authTag: str
    createdAt: datetime


class MensajeUsuarioSalida(BaseModel):
    messageId: UUID
    senderId: UUID
    recipientId: UUID | None
    groupId: UUID | None
    ciphertext: str
    encryptedKey: str
    nonce: str
    authTag: str
    createdAt: datetime


class MensajeDescifradoSalida(BaseModel):
    messageId: UUID
    senderId: UUID
    recipientId: UUID | None
    groupId: UUID | None
    plaintext: str
    createdAt: datetime
