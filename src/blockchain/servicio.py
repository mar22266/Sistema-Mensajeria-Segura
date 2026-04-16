import hashlib
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.blockchain.modelos import BloqueBlockchain

DIFICULTAD_MINADO = 3


# Construye la cadena base para hashear un bloque
def construirCadenaBloque(
    indice: int,
    timestamp: str,
    senderId: str | None,
    recipientId: str | None,
    messageHash: str,
    previousHash: str,
    nonce: int,
) -> str:
    return (
        f"{indice}|{timestamp}|{senderId or ''}|{recipientId or ''}|"
        f"{messageHash}|{previousHash}|{nonce}"
    )


# Calcula el hash SHA 256 de un bloque
def calcularHashBloque(
    indice: int,
    timestamp: str,
    senderId: str | None,
    recipientId: str | None,
    messageHash: str,
    previousHash: str,
    nonce: int,
) -> str:
    cadenaBloque = construirCadenaBloque(
        indice=indice,
        timestamp=timestamp,
        senderId=senderId,
        recipientId=recipientId,
        messageHash=messageHash,
        previousHash=previousHash,
        nonce=nonce,
    )

    return hashlib.sha256(cadenaBloque.encode("utf-8")).hexdigest()


# Mina un bloque con proof of work simplificado
def minarHashBloque(
    indice: int,
    timestamp: str,
    senderId: str | None,
    recipientId: str | None,
    messageHash: str,
    previousHash: str,
) -> tuple[int, str]:
    nonce = 0
    prefijoObjetivo = "0" * DIFICULTAD_MINADO

    while True:
        hashActual = calcularHashBloque(
            indice=indice,
            timestamp=timestamp,
            senderId=senderId,
            recipientId=recipientId,
            messageHash=messageHash,
            previousHash=previousHash,
            nonce=nonce,
        )

        if hashActual.startswith(prefijoObjetivo):
            return nonce, hashActual

        nonce += 1


# Obtiene el ultimo bloque de la cadena
def obtenerUltimoBloque(baseDatos: Session) -> BloqueBlockchain | None:
    return (
        baseDatos.query(BloqueBlockchain)
        .order_by(BloqueBlockchain.indice.desc())
        .first()
    )


# Crea el bloque genesis si la cadena esta vacia
def asegurarBloqueGenesis(baseDatos: Session) -> BloqueBlockchain:
    bloqueExistente = obtenerUltimoBloque(baseDatos)
    if bloqueExistente:
        return bloqueExistente
    indice = 0
    timestamp = datetime.now(timezone.utc)
    timestampIso = timestamp.isoformat()
    senderId = None
    recipientId = None
    messageHash = "GENESIS"
    previousHash = "0" * 64

    nonce, hashActual = minarHashBloque(
        indice=indice,
        timestamp=timestampIso,
        senderId=senderId,
        recipientId=recipientId,
        messageHash=messageHash,
        previousHash=previousHash,
    )

    bloqueGenesis = BloqueBlockchain(
        indice=indice,
        timestamp=timestamp,
        senderId=senderId,
        recipientId=recipientId,
        messageHash=messageHash,
        previousHash=previousHash,
        nonce=nonce,
        hashActual=hashActual,
    )

    baseDatos.add(bloqueGenesis)
    baseDatos.commit()
    baseDatos.refresh(bloqueGenesis)

    return bloqueGenesis


# Registra una nueva transaccion en blockchain
def registrarTransaccionBlockchain(
    baseDatos: Session, senderId: str | None, recipientId: str | None, messageHash: str
) -> BloqueBlockchain:
    asegurarBloqueGenesis(baseDatos)
    ultimoBloque = obtenerUltimoBloque(baseDatos)
    if not ultimoBloque:
        raise ValueError("No fue posible obtener el ultimo bloque")

    indice = ultimoBloque.indice + 1
    timestamp = datetime.now(timezone.utc)
    timestampIso = timestamp.isoformat()
    previousHash = ultimoBloque.hashActual

    nonce, hashActual = minarHashBloque(
        indice=indice,
        timestamp=timestampIso,
        senderId=senderId,
        recipientId=recipientId,
        messageHash=messageHash,
        previousHash=previousHash,
    )

    bloqueNuevo = BloqueBlockchain(
        indice=indice,
        timestamp=timestamp,
        senderId=senderId,
        recipientId=recipientId,
        messageHash=messageHash,
        previousHash=previousHash,
        nonce=nonce,
        hashActual=hashActual,
    )

    baseDatos.add(bloqueNuevo)
    baseDatos.commit()
    baseDatos.refresh(bloqueNuevo)

    return bloqueNuevo


# Obtiene la cadena completa ordenada
def obtenerCadenaBlockchain(baseDatos: Session) -> list[BloqueBlockchain]:
    return (
        baseDatos.query(BloqueBlockchain).order_by(BloqueBlockchain.indice.asc()).all()
    )


# Verifica integridad completa de la cadena
def verificarIntegridadBlockchain(baseDatos: Session) -> tuple[bool, str, int]:
    bloques = obtenerCadenaBlockchain(baseDatos)
    if not bloques:
        return False, "La cadena esta vacia", 0
    bloqueGenesis = bloques[0]
    if bloqueGenesis.indice != 0:
        return False, "El bloque genesis no tiene indice 0", len(bloques)
    if bloqueGenesis.previousHash != "0" * 64:
        return False, "El bloque genesis tiene previousHash invalido", len(bloques)
    for posicion, bloque in enumerate(bloques):
        timestampIso = bloque.timestamp.isoformat()

        hashRecalculado = calcularHashBloque(
            indice=bloque.indice,
            timestamp=timestampIso,
            senderId=bloque.senderId,
            recipientId=bloque.recipientId,
            messageHash=bloque.messageHash,
            previousHash=bloque.previousHash,
            nonce=bloque.nonce,
        )
        if hashRecalculado != bloque.hashActual:
            return False, f"Hash invalido en bloque {bloque.indice}", len(bloques)
        if not bloque.hashActual.startswith("0" * DIFICULTAD_MINADO):
            return (
                False,
                f"Proof of work invalido en bloque {bloque.indice}",
                len(bloques),
            )

        if posicion == 0:
            continue

        bloqueAnterior = bloques[posicion - 1]
        if bloque.indice != bloqueAnterior.indice + 1:
            return False, f"Secuencia invalida en bloque {bloque.indice}", len(bloques)
        if bloque.previousHash != bloqueAnterior.hashActual:
            return (
                False,
                f"Encadenamiento invalido en bloque {bloque.indice}",
                len(bloques),
            )

    return True, "Cadena valida", len(bloques)
