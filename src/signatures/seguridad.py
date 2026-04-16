import base64
import hashlib

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from src.auth.criptografia import descifrarLlavePrivada


# Calcula el hash SHA 256 del mensaje original
def calcularHashSha256Texto(textoPlano: str) -> str:
    return hashlib.sha256(textoPlano.encode("utf-8")).hexdigest()


# Firma el hash SHA 256 del mensaje con RSA PSS
def firmarHashMensajeRsaPss(
    messageHashHex: str, encryptedPrivateKey: str, passwordPlano: str
) -> str:
    llavePrivadaPem = descifrarLlavePrivada(passwordPlano, encryptedPrivateKey)

    llavePrivada = serialization.load_pem_private_key(
        llavePrivadaPem.encode("utf-8"), password=None
    )

    firma = llavePrivada.sign(
        messageHashHex.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256(),
    )

    return base64.b64encode(firma).decode("utf-8")


# Verifica la firma RSA PSS usando la llave publica del remitente
def verificarFirmaMensajeRsaPss(
    messageHashHex: str, firmaBase64: str, publicKeyPem: str
) -> bool:
    try:
        llavePublica = serialization.load_pem_public_key(publicKeyPem.encode("utf-8"))

        firma = base64.b64decode(firmaBase64)

        llavePublica.verify(
            firma,
            messageHashHex.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256(),
        )

        return True
    except Exception:
        return False
