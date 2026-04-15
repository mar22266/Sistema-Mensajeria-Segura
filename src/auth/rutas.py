from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.auth.baseDatos import obtenerBaseDatos
from src.auth.esquemas import RegistroUsuarioEntrada, RegistroUsuarioSalida
from src.auth.servicio import obtenerUsuarioPorEmail, registrarUsuario


routerAuth = APIRouter(prefix="/auth", tags=["auth"])


# Registra un nuevo usuario en el sistema
@routerAuth.post(
    "/register",
    response_model=RegistroUsuarioSalida,
    status_code=status.HTTP_201_CREATED,
)
def registrarUsuarioRuta(
    datosEntrada: RegistroUsuarioEntrada, baseDatos: Session = Depends(obtenerBaseDatos)
):
    usuarioExistente = obtenerUsuarioPorEmail(baseDatos, datosEntrada.email)

    if usuarioExistente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El correo ya se encuentra registrado",
        )

    usuarioCreado = registrarUsuario(
        baseDatos=baseDatos,
        displayName=datosEntrada.displayName,
        email=datosEntrada.email,
        password=datosEntrada.password,
    )

    return usuarioCreado
