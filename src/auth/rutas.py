from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.auth.baseDatos import obtenerBaseDatos
from src.auth.esquemas import (
    RegistroUsuarioEntrada,
    RegistroUsuarioSalida,
    LoginUsuarioEntrada,
    LoginUsuarioSalida,
)
from src.auth.servicio import (
    obtenerUsuarioPorEmail,
    registrarUsuario,
    autenticarUsuario,
)
from src.auth.tokens import generarTokenAcceso


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


# Inicia sesion y retorna un JWT
@routerAuth.post(
    "/login", response_model=LoginUsuarioSalida, status_code=status.HTTP_200_OK
)
def loginUsuarioRuta(
    datosEntrada: LoginUsuarioEntrada, baseDatos: Session = Depends(obtenerBaseDatos)
):
    usuario = autenticarUsuario(
        baseDatos=baseDatos, email=datosEntrada.email, password=datosEntrada.password
    )

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales invalidas"
        )

    accessToken = generarTokenAcceso(
        {
            "sub": str(usuario.id),
            "email": usuario.email,
            "displayName": usuario.displayName,
        }
    )

    return LoginUsuarioSalida(
        accessToken=accessToken,
        tokenType="bearer",
        userId=usuario.id,
        email=usuario.email,
        displayName=usuario.displayName,
    )
