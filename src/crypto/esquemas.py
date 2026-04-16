from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# clase de esquemas para la validacion de datos de entrada y salida de la API
class CrearGrupoEntrada(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    creadoPor: UUID
    miembrosIds: list[UUID] = Field(min_length=1)


# clase de esquema para la salida de datos del grupo creado
class CrearGrupoSalida(BaseModel):
    groupId: UUID
    nombre: str
    creadoPor: UUID
    miembrosIds: list[UUID]
    createdAt: datetime


# clase para la entrada de datos del envio de un mensaje
class EnviarMensajeEntrada(BaseModel):
    senderId: UUID
    senderPassword: str = Field(min_length=8, max_length=128)
    plaintext: str = Field(min_length=1)


# clase para la entrada de datos del envio de un mensaje grupal
class EnviarMensajeGrupoEntrada(BaseModel):
    senderId: UUID
    senderPassword: str = Field(min_length=8, max_length=128)
    plaintext: str = Field(min_length=1)


# clase de esquema para la salida de datos del envio de un mensaje
class EnviarMensajeSalida(BaseModel):
    messageId: UUID
    senderId: UUID
    recipientId: UUID | None
    groupId: UUID | None
    ciphertext: str
    encryptedKey: str
    nonce: str
    authTag: str
    signature: str | None
    createdAt: datetime


# clase para la salida de datos del envio de un mensaje grupal
class EnviarMensajeGrupoSalida(BaseModel):
    messageId: UUID
    senderId: UUID
    groupId: UUID
    ciphertext: str
    nonce: str
    authTag: str
    signature: str | None
    encryptedKeysGeneradas: int
    createdAt: datetime


# clase para la salida de mensajes cifrados de un usuario
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


# clase para la salida de mensajes descifrados de un usuario
class MensajeDescifradoSalida(BaseModel):
    messageId: UUID
    senderId: UUID
    recipientId: UUID | None
    groupId: UUID | None
    plaintext: str
    signature: str | None
    estadoFirma: str
    firmaVerificada: bool
    alerta: str | None
    createdAt: datetime


# clase para recuperar mensajes descifrados de un usuario
class RecuperarMensajesSalida(BaseModel):
    userId: UUID
    mensajes: list[MensajeDescifradoSalida]
