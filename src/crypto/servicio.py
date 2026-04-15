from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.auth.modelos import Usuario
from src.crypto.modelos import Mensaje
from src.crypto.seguridad import (
    cifrarClaveAesConRsaOaep,
    cifrarMensajeAesGcm,
    descifrarClaveAesConRsaOaep,
    descifrarMensajeAesGcm,
    generarClaveAesEfimera,
)


# Busca un usuario por id
def obtenerUsuarioPorId(baseDatos: Session, userId: UUID) -> Usuario | None:
    return baseDatos.query(Usuario).filter(Usuario.id == userId).first()


# Crea y almacena un mensaje individual cifrado
def enviarMensajeIndividual(
    baseDatos: Session, senderId: UUID, destId: UUID, plaintext: str
) -> Mensaje:
    remitente = obtenerUsuarioPorId(baseDatos, senderId)
    destinatario = obtenerUsuarioPorId(baseDatos, destId)

    if not remitente or not destinatario:
        raise ValueError("Remitente o destinatario no encontrado")

    claveAes = generarClaveAesEfimera()

    ciphertext, nonce, authTag = cifrarMensajeAesGcm(
        textoPlano=plaintext, claveAes=claveAes
    )

    encryptedKey = cifrarClaveAesConRsaOaep(
        claveAes=claveAes, llavePublicaPem=destinatario.publicKey
    )

    mensajeNuevo = Mensaje(
        senderId=senderId,
        recipientId=destId,
        groupId=None,
        ciphertext=ciphertext,
        encryptedKey=encryptedKey,
        nonce=nonce,
        authTag=authTag,
        signature=None,
    )

    baseDatos.add(mensajeNuevo)
    baseDatos.commit()
    baseDatos.refresh(mensajeNuevo)

    return mensajeNuevo


# Obtiene los mensajes individuales recibidos por un usuario
def obtenerMensajesRecibidosUsuario(baseDatos: Session, userId: UUID) -> list[Mensaje]:
    return (
        baseDatos.query(Mensaje)
        .filter(Mensaje.recipientId == userId)
        .order_by(Mensaje.createdAt.asc())
        .all()
    )


# Descifra un mensaje individual para el usuario destinatario
def descifrarMensajeIndividualUsuario(
    mensaje: Mensaje, usuarioDestino: Usuario, passwordPlano: str
) -> str:
    if not mensaje.encryptedKey:
        raise ValueError("El mensaje no contiene clave cifrada individual")

    claveAes = descifrarClaveAesConRsaOaep(
        encryptedKeyBase64=mensaje.encryptedKey,
        encryptedPrivateKey=usuarioDestino.encryptedPrivateKey,
        passwordPlano=passwordPlano,
    )

    return descifrarMensajeAesGcm(
        ciphertextBase64=mensaje.ciphertext,
        nonceBase64=mensaje.nonce,
        authTagBase64=mensaje.authTag,
        claveAes=claveAes,
    )


# Recupera y descifra los mensajes de un usuario
def recuperarMensajesDescifradosUsuario(
    baseDatos: Session, userId: UUID, passwordPlano: str
) -> list[dict]:
    usuario = obtenerUsuarioPorId(baseDatos, userId)

    if not usuario:
        raise ValueError("Usuario no encontrado")

    mensajes = obtenerMensajesRecibidosUsuario(baseDatos, userId)

    mensajesDescifrados = []

    for mensaje in mensajes:
        plaintext = descifrarMensajeIndividualUsuario(
            mensaje=mensaje, usuarioDestino=usuario, passwordPlano=passwordPlano
        )

        mensajesDescifrados.append(
            {
                "messageId": mensaje.id,
                "senderId": mensaje.senderId,
                "recipientId": mensaje.recipientId,
                "groupId": mensaje.groupId,
                "plaintext": plaintext,
                "createdAt": mensaje.createdAt,
            }
        )

    return mensajesDescifrados
