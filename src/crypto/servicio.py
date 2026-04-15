from uuid import UUID

from sqlalchemy.orm import Session

from src.auth.modelos import Usuario
from src.crypto.modelos import Mensaje
from src.crypto.seguridad import (
    cifrarClaveAesConRsaOaep,
    cifrarMensajeAesGcm,
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
