from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.auth.baseDatos import obtenerBaseDatos
from src.auth.modelos import Usuario
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


# Obtiene el usuario autenticado actual desde el token
def obtenerUsuarioActual(
    datosToken: dict = Depends(obtenerTokenActual),
    baseDatos: Session = Depends(obtenerBaseDatos),
) -> Usuario:
    userId = datosToken.get("sub")

    if not userId:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El token no contiene un identificador de usuario valido",
        )

    usuario = baseDatos.query(Usuario).filter(Usuario.id == UUID(userId)).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario autenticado no existe",
        )

    return usuario
