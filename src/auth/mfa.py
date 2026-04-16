import base64
from io import BytesIO
from urllib.parse import quote

import pyotp
import qrcode

from src.auth.configuracion import configuracion


# Genera un secreto TOTP en base32
def generarSecretoTotp() -> str:
    return pyotp.random_base32()


# Construye la url otpauth para apps autenticadoras
def construirUrlTotp(email: str, secretoTotp: str) -> str:
    nombreAplicacion = quote(configuracion.APPNombre)
    emailSeguro = quote(email)

    return (
        f"otpauth://totp/{nombreAplicacion}:{emailSeguro}"
        f"?secret={secretoTotp}&issuer={nombreAplicacion}"
    )


# Genera una imagen QR en base64 a partir del otpauth url
def generarQrBase64(otpauthUrl: str) -> str:
    imagenQr = qrcode.make(otpauthUrl)

    buffer = BytesIO()
    imagenQr.save(buffer, format="PNG")
    contenido = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{contenido}"


# Verifica un codigo TOTP
def verificarCodigoTotp(secretoTotp: str, codigo: str) -> bool:
    totp = pyotp.TOTP(secretoTotp)
    return totp.verify(codigo, valid_window=1)
