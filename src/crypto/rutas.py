from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.auth.baseDatos import obtenerBaseDatos
from src.crypto.esquemas import EnviarMensajeEntrada, EnviarMensajeSalida
from src.crypto.servicio import enviarMensajeIndividual


routerMessages = APIRouter(tags=["messages"])


# Envia un mensaje individual cifrado
@routerMessages.post(
    "/messages/{destId}",
    response_model=EnviarMensajeSalida,
    status_code=status.HTTP_201_CREATED,
)
def enviarMensajeRuta(
    destId: UUID,
    datosEntrada: EnviarMensajeEntrada,
    baseDatos: Session = Depends(obtenerBaseDatos),
):
    try:
        mensaje = enviarMensajeIndividual(
            baseDatos=baseDatos,
            senderId=datosEntrada.senderId,
            destId=destId,
            plaintext=datosEntrada.plaintext,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error

    return EnviarMensajeSalida(
        messageId=mensaje.id,
        senderId=mensaje.senderId,
        recipientId=mensaje.recipientId,
        groupId=mensaje.groupId,
        ciphertext=mensaje.ciphertext,
        encryptedKey=mensaje.encryptedKey or "",
        nonce=mensaje.nonce,
        authTag=mensaje.authTag,
        createdAt=mensaje.createdAt,
    )
