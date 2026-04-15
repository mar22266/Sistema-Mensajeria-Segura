from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.auth.baseDatos import obtenerBaseDatos
from src.crypto.esquemas import (
    CrearGrupoEntrada,
    CrearGrupoSalida,
    EnviarMensajeEntrada,
    EnviarMensajeGrupoEntrada,
    EnviarMensajeGrupoSalida,
    EnviarMensajeSalida,
    RecuperarMensajesSalida,
)
from src.crypto.servicio import (
    crearGrupo,
    enviarMensajeGrupal,
    enviarMensajeIndividual,
    recuperarMensajesDescifradosUsuario,
)


routerMessages = APIRouter(tags=["messages", "groups"])


# Crea un grupo y registra sus miembros
@routerMessages.post(
    "/groups", response_model=CrearGrupoSalida, status_code=status.HTTP_201_CREATED
)
def crearGrupoRuta(
    datosEntrada: CrearGrupoEntrada, baseDatos: Session = Depends(obtenerBaseDatos)
):
    try:
        grupo, miembrosIds = crearGrupo(
            baseDatos=baseDatos,
            nombre=datosEntrada.nombre,
            creadoPor=datosEntrada.creadoPor,
            miembrosIds=datosEntrada.miembrosIds,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error

    return CrearGrupoSalida(
        groupId=grupo.id,
        nombre=grupo.nombre,
        creadoPor=grupo.creadoPor,
        miembrosIds=miembrosIds,
        createdAt=grupo.createdAt,
    )


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


# Envia un mensaje grupal cifrado
@routerMessages.post(
    "/groups/{groupId}/messages",
    response_model=EnviarMensajeGrupoSalida,
    status_code=status.HTTP_201_CREATED,
)
def enviarMensajeGrupalRuta(
    groupId: UUID,
    datosEntrada: EnviarMensajeGrupoEntrada,
    baseDatos: Session = Depends(obtenerBaseDatos),
):
    try:
        mensaje, encryptedKeysGeneradas = enviarMensajeGrupal(
            baseDatos=baseDatos,
            senderId=datosEntrada.senderId,
            groupId=groupId,
            plaintext=datosEntrada.plaintext,
        )
    except ValueError as error:
        detalle = str(error)

        if detalle in {
            "El remitente no existe",
            "El grupo no existe",
            "El grupo no tiene miembros",
        }:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=detalle
            ) from error

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=detalle
        ) from error

    return EnviarMensajeGrupoSalida(
        messageId=mensaje.id,
        senderId=mensaje.senderId,
        groupId=mensaje.groupId,
        ciphertext=mensaje.ciphertext,
        nonce=mensaje.nonce,
        authTag=mensaje.authTag,
        encryptedKeysGeneradas=encryptedKeysGeneradas,
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
