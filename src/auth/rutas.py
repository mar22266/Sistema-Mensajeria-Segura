from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.auth.baseDatos import obtenerBaseDatos
from src.auth.esquemas import (
    HabilitarMfaEntrada,
    HabilitarMfaSalida,
    LoginMfaEntrada,
    LoginMfaSalida,
    LoginUsuarioEntrada,
    LoginUsuarioSalida,
    RefreshTokenEntrada,
    RefreshTokenSalida,
    RegistroUsuarioEntrada,
    RegistroUsuarioSalida,
    VerificarMfaEntrada,
    VerificarMfaSalida,
)
from src.auth.servicio import (
    completarLoginConMfa,
    habilitarMfaUsuario,
    obtenerUsuarioPorEmail,
    procesarLoginUsuario,
    refrescarSesionUsuario,
    registrarUsuario,
    verificarMfaUsuario,
)


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


# Inicia sesion considerando si MFA esta activo
@routerAuth.post(
    "/login", response_model=LoginUsuarioSalida, status_code=status.HTTP_200_OK
)
def loginUsuarioRuta(
    datosEntrada: LoginUsuarioEntrada, baseDatos: Session = Depends(obtenerBaseDatos)
):
    try:
        resultado = procesarLoginUsuario(
            baseDatos=baseDatos,
            email=datosEntrada.email,
            password=datosEntrada.password,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)
        ) from error

    return LoginUsuarioSalida(**resultado)


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


# Completa el login con password y TOTP y emite tokens
@routerAuth.post(
    "/mfa/login", response_model=LoginMfaSalida, status_code=status.HTTP_200_OK
)
def loginConMfaRuta(
    datosEntrada: LoginMfaEntrada, baseDatos: Session = Depends(obtenerBaseDatos)
):
    try:
        resultado = completarLoginConMfa(
            baseDatos=baseDatos,
            email=datosEntrada.email,
            password=datosEntrada.password,
            codigoTotp=datosEntrada.codigoTotp,
        )
    except ValueError as error:
        detalle = str(error)

        if detalle == "Credenciales invalidas":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=detalle
            ) from error

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=detalle
        ) from error

    return LoginMfaSalida(**resultado)


# Refresca una sesion a partir de refresh token
@routerAuth.post(
    "/refresh", response_model=RefreshTokenSalida, status_code=status.HTTP_200_OK
)
def refrescarTokenRuta(datosEntrada: RefreshTokenEntrada):
    try:
        resultado = refrescarSesionUsuario(datosEntrada.refreshToken)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido o expirado",
        ) from error

    return RefreshTokenSalida(**resultado)
