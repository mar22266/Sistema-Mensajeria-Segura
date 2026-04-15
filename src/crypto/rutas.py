from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.auth.baseDatos import obtenerBaseDatos
from src.crypto.esquemas import (
    EnviarMensajeEntrada,
    EnviarMensajeSalida,
    RecuperarMensajesSalida,
)
from src.crypto.servicio import (
    enviarMensajeIndividual,
    recuperarMensajesDescifradosUsuario,
)


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


# Recupera y descifra los mensajes de un usuario
@routerMessages.get(
    "/messages/{userId}",
    response_model=RecuperarMensajesSalida,
    status_code=status.HTTP_200_OK,
)
def obtenerMensajesUsuarioRuta(
    userId: UUID,
    password: str = Query(..., min_length=8),
    baseDatos: Session = Depends(obtenerBaseDatos),
):
    try:
        mensajes = recuperarMensajesDescifradosUsuario(
            baseDatos=baseDatos, userId=userId, passwordPlano=password
        )
    except ValueError as error:
        mensajeError = str(error)

        if mensajeError == "Usuario no encontrado":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=mensajeError
            ) from error

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=mensajeError
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fue posible descifrar los mensajes con los datos proporcionados",
        ) from error

    return RecuperarMensajesSalida(userId=userId, mensajes=mensajes)
