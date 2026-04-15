import base64
import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from src.auth.criptografia import descifrarLlavePrivada


# Genera una clave AES 256 efimera
def generarClaveAesEfimera() -> bytes:
    return os.urandom(32)


# Cifra plaintext con AES 256 GCM
def cifrarMensajeAesGcm(textoPlano: str, claveAes: bytes) -> tuple[str, str, str]:
    nonce = os.urandom(12)
    cifrador = AESGCM(claveAes)

    contenidoCompleto = cifrador.encrypt(nonce, textoPlano.encode("utf-8"), None)

    ciphertext = contenidoCompleto[:-16]
    authTag = contenidoCompleto[-16:]

    return (
        base64.b64encode(ciphertext).decode("utf-8"),
        base64.b64encode(nonce).decode("utf-8"),
        base64.b64encode(authTag).decode("utf-8"),
    )


# Descifra mensaje AES 256 GCM
def descifrarMensajeAesGcm(
    ciphertextBase64: str, nonceBase64: str, authTagBase64: str, claveAes: bytes
) -> str:
    ciphertext = base64.b64decode(ciphertextBase64)
    nonce = base64.b64decode(nonceBase64)
    authTag = base64.b64decode(authTagBase64)

    contenidoCompleto = ciphertext + authTag

    cifrador = AESGCM(claveAes)
    textoPlano = cifrador.decrypt(nonce, contenidoCompleto, None)

    return textoPlano.decode("utf-8")


# Cifra la clave AES con la llave publica RSA del destinatario
def cifrarClaveAesConRsaOaep(claveAes: bytes, llavePublicaPem: str) -> str:
    llavePublica = serialization.load_pem_public_key(llavePublicaPem.encode("utf-8"))

    claveCifrada = llavePublica.encrypt(
        claveAes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    return base64.b64encode(claveCifrada).decode("utf-8")


# Descifra la clave AES usando la llave privada del usuario
def descifrarClaveAesConRsaOaep(
    encryptedKeyBase64: str, encryptedPrivateKey: str, passwordPlano: str
) -> bytes:
    llavePrivadaPem = descifrarLlavePrivada(passwordPlano, encryptedPrivateKey)

    llavePrivada = serialization.load_pem_private_key(
        llavePrivadaPem.encode("utf-8"), password=None
    )

    claveCifrada = base64.b64decode(encryptedKeyBase64)

    return llavePrivada.decrypt(
        claveCifrada,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
