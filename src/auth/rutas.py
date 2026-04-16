from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.auth.baseDatos import obtenerBaseDatos
from src.auth.esquemas import (
    HabilitarMfaEntrada,
    HabilitarMfaSalida,
    LoginUsuarioEntrada,
    LoginUsuarioSalida,
    RegistroUsuarioEntrada,
    RegistroUsuarioSalida,
    VerificarMfaEntrada,
    VerificarMfaSalida,
)
from src.auth.servicio import (
    autenticarUsuario,
    habilitarMfaUsuario,
    obtenerUsuarioPorEmail,
    registrarUsuario,
    verificarMfaUsuario,
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


# Activa MFA para un usuario y retorna QR TOTP
@routerAuth.post(
    "/mfa/enable", response_model=HabilitarMfaSalida, status_code=status.HTTP_200_OK
)
def habilitarMfaRuta(
    datosEntrada: HabilitarMfaEntrada, baseDatos: Session = Depends(obtenerBaseDatos)
):
    try:
        resultado = habilitarMfaUsuario(baseDatos=baseDatos, userId=datosEntrada.userId)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error

    return HabilitarMfaSalida(**resultado)


# Verifica codigo TOTP del usuario
@routerAuth.post(
    "/mfa/verify", response_model=VerificarMfaSalida, status_code=status.HTTP_200_OK
)
def verificarMfaRuta(
    datosEntrada: VerificarMfaEntrada, baseDatos: Session = Depends(obtenerBaseDatos)
):
    try:
        resultado = verificarMfaUsuario(
            baseDatos=baseDatos,
            email=datosEntrada.email,
            codigoTotp=datosEntrada.codigoTotp,
        )
    except ValueError as error:
        detalle = str(error)

        if detalle == "Usuario no encontrado":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=detalle
            ) from error

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=detalle
        ) from error

    return VerificarMfaSalida(**resultado)
