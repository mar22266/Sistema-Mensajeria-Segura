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


# clase para la entrada de datos del login de usuario
class LoginUsuarioEntrada(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


# clase para la salida de datos del login de usuario
class LoginUsuarioSalida(BaseModel):
    accessToken: str | None
    refreshToken: str | None
    tokenType: str
    userId: UUID
    email: EmailStr
    displayName: str
    mfaActiva: bool
    requiereMfa: bool
    mensaje: str


# clase para la entrada de datos del refresh token
class RefreshTokenEntrada(BaseModel):
    refreshToken: str


# clase para la salida de datos del refresh token
class RefreshTokenSalida(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str


# clase para la entrada de datos de habilitacion de MFA
class HabilitarMfaEntrada(BaseModel):
    userId: UUID


# clase para la salida de datos de habilitacion de MFA
class HabilitarMfaSalida(BaseModel):
    userId: UUID
    email: EmailStr
    mfaActiva: bool
    otpauthUrl: str
    qrBase64: str


# clase para la entrada de datos de verificacion de MFA
class VerificarMfaEntrada(BaseModel):
    email: EmailStr
    codigoTotp: str = Field(min_length=6, max_length=6)


# clase para la salida de datos de verificacion de MFA
class VerificarMfaSalida(BaseModel):
    email: EmailStr
    codigoValido: bool
    mensaje: str


# clase de login con MFA
class LoginMfaEntrada(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    codigoTotp: str = Field(min_length=6, max_length=6)


# clase para la salida de datos del login con MFA
class LoginMfaSalida(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str
    userId: UUID
    email: EmailStr
    displayName: str
    mensaje: str


# clase para la salida de datos de la llave publica de un usuario
class LlavePublicaUsuarioSalida(BaseModel):
    userId: UUID
    email: EmailStr
    publicKey: str


# clase para la salida de datos del estado del servicio
class EstadoServicioSalida(BaseModel):
    estado: str
    servicio: str
    version: str
