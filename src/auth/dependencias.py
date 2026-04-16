from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.tokens import decodificarToken


esquemaBearer = HTTPBearer(auto_error=False)


# Obtiene y valida el token de acceso actual
def obtenerTokenActual(
    credenciales: HTTPAuthorizationCredentials = Depends(esquemaBearer),
) -> dict:
    if not credenciales:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere token de acceso",
        )

    token = credenciales.credentials
    try:
        datosToken = decodificarToken(token)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido o expirado"
        ) from error

    if datosToken.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token proporcionado no es un access token valido",
        )

    return datosToken
