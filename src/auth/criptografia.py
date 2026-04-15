import base64
import json
import os

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# Genera un par de llaves RSA 2048
def generarParLlavesUsuario() -> tuple[str, str]:
    llavePrivada = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    llavePublica = llavePrivada.public_key()
    llavePrivadaPem = llavePrivada.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    llavePublicaPem = llavePublica.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    return llavePublicaPem, llavePrivadaPem


# Deriva una clave segura desde la contrasena del usuario
def derivarClaveDesdePassword(passwordPlano: str, salt: bytes) -> bytes:
    derivador = PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600000
    )
    return derivador.derive(passwordPlano.encode("utf-8"))


# Cifra la llave privada con una clave derivada de la contrasena
def cifrarLlavePrivada(passwordPlano: str, llavePrivadaPem: str) -> str:
    salt = os.urandom(16)
    nonce = os.urandom(12)
    clave = derivarClaveDesdePassword(passwordPlano, salt)
    cifrador = AESGCM(clave)
    textoCifrado = cifrador.encrypt(nonce, llavePrivadaPem.encode("utf-8"), None)
    contenidoCifrado = {
        "algoritmo": "AESGCM",
        "kdf": "PBKDF2HMAC-SHA256",
        "iteraciones": 600000,
        "salt": base64.b64encode(salt).decode("utf-8"),
        "nonce": base64.b64encode(nonce).decode("utf-8"),
        "textoCifrado": base64.b64encode(textoCifrado).decode("utf-8"),
    }

    return json.dumps(contenidoCifrado)


# Descifra la llave privada almacenada
def descifrarLlavePrivada(passwordPlano: str, contenidoCifrado: str) -> str:
    datos = json.loads(contenidoCifrado)
    salt = base64.b64decode(datos["salt"])
    nonce = base64.b64decode(datos["nonce"])
    textoCifrado = base64.b64decode(datos["textoCifrado"])
    clave = derivarClaveDesdePassword(passwordPlano, salt)
    cifrador = AESGCM(clave)
    llavePrivada = cifrador.decrypt(nonce, textoCifrado, None)

    return llavePrivada.decode("utf-8")
