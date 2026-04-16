from uuid import UUID

from sqlalchemy.orm import Session

from src.auth.modelos import Usuario
from src.blockchain.servicio import registrarTransaccionBlockchain
from src.crypto.modelos import Grupo, GrupoMiembro, Mensaje, MensajeDestinatario
from src.crypto.seguridad import (
    cifrarClaveAesConRsaOaep,
    cifrarMensajeAesGcm,
    descifrarClaveAesConRsaOaep,
    descifrarMensajeAesGcm,
    generarClaveAesEfimera,
)
from src.signatures.seguridad import calcularHashSha256Texto, firmarHashMensajeRsaPss


# Busca un usuario por id
def obtenerUsuarioPorId(baseDatos: Session, userId: UUID) -> Usuario | None:
    return baseDatos.query(Usuario).filter(Usuario.id == userId).first()


# Busca un grupo por id
def obtenerGrupoPorId(baseDatos: Session, groupId: UUID) -> Grupo | None:
    return baseDatos.query(Grupo).filter(Grupo.id == groupId).first()


# Obtiene los miembros de un grupo
def obtenerMiembrosGrupo(baseDatos: Session, groupId: UUID) -> list[GrupoMiembro]:
    return baseDatos.query(GrupoMiembro).filter(GrupoMiembro.groupId == groupId).all()


# Crea un grupo y registra sus miembros
def crearGrupo(
    baseDatos: Session, nombre: str, creadoPor: UUID, miembrosIds: list[UUID]
) -> tuple[Grupo, list[UUID]]:
    creador = obtenerUsuarioPorId(baseDatos, creadoPor)

    if not creador:
        raise ValueError("El usuario creador no existe")

    miembrosUnicos = []
    miembrosVistos = set()

    for miembroId in [creadoPor, *miembrosIds]:
        if miembroId not in miembrosVistos:
            miembrosVistos.add(miembroId)
            miembrosUnicos.append(miembroId)

    usuariosExistentes = []
    for miembroId in miembrosUnicos:
        usuario = obtenerUsuarioPorId(baseDatos, miembroId)
        if not usuario:
            raise ValueError("Uno o mas miembros no existen")
        usuariosExistentes.append(usuario)

    grupoNuevo = Grupo(nombre=nombre.strip(), creadoPor=creadoPor)

    baseDatos.add(grupoNuevo)
    baseDatos.flush()

    for usuario in usuariosExistentes:
        miembro = GrupoMiembro(groupId=grupoNuevo.id, userId=usuario.id)
        baseDatos.add(miembro)

    baseDatos.commit()
    baseDatos.refresh(grupoNuevo)

    return grupoNuevo, [usuario.id for usuario in usuariosExistentes]


# Crea y almacena un mensaje individual cifrado y firmado
def enviarMensajeIndividual(
    baseDatos: Session,
    senderId: UUID,
    destId: UUID,
    senderPassword: str,
    plaintext: str,
) -> Mensaje:
    remitente = obtenerUsuarioPorId(baseDatos, senderId)
    destinatario = obtenerUsuarioPorId(baseDatos, destId)

    if not remitente or not destinatario:
        raise ValueError("Remitente o destinatario no encontrado")

    messageHash = calcularHashSha256Texto(plaintext)

    signature = firmarHashMensajeRsaPss(
        messageHashHex=messageHash,
        encryptedPrivateKey=remitente.encryptedPrivateKey,
        passwordPlano=senderPassword,
    )

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
        signature=signature,
    )

    baseDatos.add(mensajeNuevo)
    baseDatos.commit()
    baseDatos.refresh(mensajeNuevo)

    registrarTransaccionBlockchain(
        baseDatos=baseDatos,
        senderId=str(senderId),
        recipientId=str(destId),
        messageHash=messageHash,
    )

    return mensajeNuevo


# Crea y almacena un mensaje grupal cifrado y firmado
def enviarMensajeGrupal(
    baseDatos: Session,
    senderId: UUID,
    groupId: UUID,
    senderPassword: str,
    plaintext: str,
) -> tuple[Mensaje, int]:
    remitente = obtenerUsuarioPorId(baseDatos, senderId)
    grupo = obtenerGrupoPorId(baseDatos, groupId)

    if not remitente:
        raise ValueError("El remitente no existe")

    if not grupo:
        raise ValueError("El grupo no existe")

    miembrosGrupo = obtenerMiembrosGrupo(baseDatos, groupId)

    if not miembrosGrupo:
        raise ValueError("El grupo no tiene miembros")

    idsMiembros = [miembro.userId for miembro in miembrosGrupo]

    if senderId not in idsMiembros:
        raise ValueError("El remitente no pertenece al grupo")

    messageHash = calcularHashSha256Texto(plaintext)

    signature = firmarHashMensajeRsaPss(
        messageHashHex=messageHash,
        encryptedPrivateKey=remitente.encryptedPrivateKey,
        passwordPlano=senderPassword,
    )

    claveAes = generarClaveAesEfimera()

    ciphertext, nonce, authTag = cifrarMensajeAesGcm(
        textoPlano=plaintext, claveAes=claveAes
    )

    mensajeNuevo = Mensaje(
        senderId=senderId,
        recipientId=None,
        groupId=groupId,
        ciphertext=ciphertext,
        encryptedKey=None,
        nonce=nonce,
        authTag=authTag,
        signature=signature,
    )

    baseDatos.add(mensajeNuevo)
    baseDatos.flush()

    cantidadEncryptedKeys = 0

    for miembroId in idsMiembros:
        usuarioMiembro = obtenerUsuarioPorId(baseDatos, miembroId)

        if not usuarioMiembro:
            continue

        encryptedKey = cifrarClaveAesConRsaOaep(
            claveAes=claveAes, llavePublicaPem=usuarioMiembro.publicKey
        )

        mensajeDestinatario = MensajeDestinatario(
            messageId=mensajeNuevo.id,
            userId=usuarioMiembro.id,
            encryptedKey=encryptedKey,
        )

        baseDatos.add(mensajeDestinatario)
        cantidadEncryptedKeys += 1

    baseDatos.commit()
    baseDatos.refresh(mensajeNuevo)

    registrarTransaccionBlockchain(
        baseDatos=baseDatos,
        senderId=str(senderId),
        recipientId=str(groupId),
        messageHash=messageHash,
    )

    return mensajeNuevo, cantidadEncryptedKeys


# Obtiene los mensajes individuales recibidos por un usuario
def obtenerMensajesIndividualesRecibidosUsuario(
    baseDatos: Session, userId: UUID
) -> list[Mensaje]:
    return (
        baseDatos.query(Mensaje)
        .filter(Mensaje.recipientId == userId)
        .order_by(Mensaje.createdAt.asc())
        .all()
    )


# Obtiene los mensajes grupales que puede leer un usuario
def obtenerMensajesGrupalesUsuario(
    baseDatos: Session, userId: UUID
) -> list[tuple[Mensaje, MensajeDestinatario]]:
    registros = (
        baseDatos.query(Mensaje, MensajeDestinatario)
        .join(MensajeDestinatario, MensajeDestinatario.messageId == Mensaje.id)
        .filter(MensajeDestinatario.userId == userId)
        .filter(Mensaje.groupId.is_not(None))
        .order_by(Mensaje.createdAt.asc())
        .all()
    )

    return registros


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


# Descifra un mensaje grupal para un usuario miembro
def descifrarMensajeGrupalUsuario(
    mensaje: Mensaje,
    mensajeDestinatario: MensajeDestinatario,
    usuarioDestino: Usuario,
    passwordPlano: str,
) -> str:
    claveAes = descifrarClaveAesConRsaOaep(
        encryptedKeyBase64=mensajeDestinatario.encryptedKey,
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

    mensajesDescifrados = []

    mensajesIndividuales = obtenerMensajesIndividualesRecibidosUsuario(
        baseDatos, userId
    )

    for mensaje in mensajesIndividuales:
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

    mensajesGrupales = obtenerMensajesGrupalesUsuario(baseDatos, userId)

    for mensaje, mensajeDestinatario in mensajesGrupales:
        plaintext = descifrarMensajeGrupalUsuario(
            mensaje=mensaje,
            mensajeDestinatario=mensajeDestinatario,
            usuarioDestino=usuario,
            passwordPlano=passwordPlano,
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

    mensajesDescifrados.sort(key=lambda mensaje: mensaje["createdAt"])

    return mensajesDescifrados
