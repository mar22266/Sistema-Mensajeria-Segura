from datetime import UTC, datetime, timedelta

import jwt

from src.auth.configuracion import configuracion


# Genera un token JWT para el usuario autenticado
def generarTokenAcceso(datos: dict) -> str:
    datosToken = datos.copy()
    fechaExpiracion = datetime.now(UTC) + timedelta(
        minutes=configuracion.JWTMinutosExpiracion
    )

    datosToken["exp"] = fechaExpiracion
    datosToken["iat"] = datetime.now(UTC)

    return jwt.encode(
        datosToken, configuracion.JWTClaveSecreta, algorithm=configuracion.JWTAlgoritmo
    )
