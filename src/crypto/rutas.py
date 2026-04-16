from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.auth.baseDatos import obtenerBaseDatos
from src.auth.dependencias import obtenerUsuarioActual
from src.auth.modelos import Usuario
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
    datosEntrada: CrearGrupoEntrada,
    usuarioActual: Usuario = Depends(obtenerUsuarioActual),
    baseDatos: Session = Depends(obtenerBaseDatos),
):
    if str(usuarioActual.id) != str(datosEntrada.creadoPor):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede crear un grupo en nombre de otro usuario",
        )

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


# Envia un mensaje individual cifrado y firmado
@routerMessages.post(
    "/messages/{destId}",
    response_model=EnviarMensajeSalida,
    status_code=status.HTTP_201_CREATED,
)
def enviarMensajeRuta(
    destId: UUID,
    datosEntrada: EnviarMensajeEntrada,
    usuarioActual: Usuario = Depends(obtenerUsuarioActual),
    baseDatos: Session = Depends(obtenerBaseDatos),
):
    if str(usuarioActual.id) != str(datosEntrada.senderId):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede enviar mensajes en nombre de otro usuario",
        )

    try:
        mensaje = enviarMensajeIndividual(
            baseDatos=baseDatos,
            senderId=datosEntrada.senderId,
            destId=destId,
            senderPassword=datosEntrada.senderPassword,
            plaintext=datosEntrada.plaintext,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fue posible firmar y enviar el mensaje",
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
        signature=mensaje.signature,
        createdAt=mensaje.createdAt,
    )


# Envia un mensaje grupal cifrado y firmado
@routerMessages.post(
    "/groups/{groupId}/messages",
    response_model=EnviarMensajeGrupoSalida,
    status_code=status.HTTP_201_CREATED,
)
def enviarMensajeGrupalRuta(
    groupId: UUID,
    datosEntrada: EnviarMensajeGrupoEntrada,
    usuarioActual: Usuario = Depends(obtenerUsuarioActual),
    baseDatos: Session = Depends(obtenerBaseDatos),
):
    if str(usuarioActual.id) != str(datosEntrada.senderId):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede enviar mensajes grupales en nombre de otro usuario",
        )

    try:
        mensaje, encryptedKeysGeneradas = enviarMensajeGrupal(
            baseDatos=baseDatos,
            senderId=datosEntrada.senderId,
            groupId=groupId,
            senderPassword=datosEntrada.senderPassword,
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
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fue posible firmar y enviar el mensaje grupal",
        ) from error

    return EnviarMensajeGrupoSalida(
        messageId=mensaje.id,
        senderId=mensaje.senderId,
        groupId=mensaje.groupId,
        ciphertext=mensaje.ciphertext,
        nonce=mensaje.nonce,
        authTag=mensaje.authTag,
        signature=mensaje.signature,
        encryptedKeysGeneradas=encryptedKeysGeneradas,
        createdAt=mensaje.createdAt,
    )


# Recupera y descifra los mensajes del usuario autenticado
@routerMessages.get(
    "/messages/{userId}",
    response_model=RecuperarMensajesSalida,
    status_code=status.HTTP_200_OK,
)
def obtenerMensajesUsuarioRuta(
    userId: UUID,
    password: str = Query(..., min_length=8),
    usuarioActual: Usuario = Depends(obtenerUsuarioActual),
    baseDatos: Session = Depends(obtenerBaseDatos),
):
    if str(usuarioActual.id) != str(userId):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puede recuperar mensajes de otro usuario",
        )

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
