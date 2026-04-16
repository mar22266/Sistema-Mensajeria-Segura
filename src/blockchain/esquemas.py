from datetime import datetime

from pydantic import BaseModel


# clase de esquemas de blockchain para la validacion de datos de entrada y salida
class BloqueBlockchainSalida(BaseModel):
    indice: int
    timestamp: datetime
    senderId: str | None
    recipientId: str | None
    messageHash: str
    previousHash: str
    nonce: int
    hashActual: str


# clase de esquema para la salida de la verificacion de la blockchain
class VerificacionBlockchainSalida(BaseModel):
    esValida: bool
    cantidadBloques: int
    detalle: str
