from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# clase de esquemas para la validacion de datos de entrada y salida de la API
# c;ase de grupo de entrada
class CrearGrupoEntrada(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    creadoPor: UUID
    miembrosIds: list[UUID] = Field(min_length=1)


# clase de salida de grupo
class CrearGrupoSalida(BaseModel):
    groupId: UUID
    nombre: str
    creadoPor: UUID
    miembrosIds: list[UUID]
    createdAt: datetime


# clase de entrada para enviar mensaje
class EnviarMensajeEntrada(BaseModel):
    senderId: UUID
    plaintext: str = Field(min_length=1)


# clase de salida para enviar mensaje
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


# clase de salida para mensaje descifrado
class MensajeDescifradoSalida(BaseModel):
    messageId: UUID
    senderId: UUID
    recipientId: UUID | None
    groupId: UUID | None
    plaintext: str
    createdAt: datetime
