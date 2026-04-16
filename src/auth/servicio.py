from uuid import UUID

from sqlalchemy.orm import Session
from src.auth.criptografia import cifrarLlavePrivada, generarParLlavesUsuario
from src.auth.mfa import (
    construirUrlTotp,
    generarQrBase64,
    generarSecretoTotp,
    verificarCodigoTotp,
)
from src.auth.modelos import Usuario
from src.auth.seguridad import generarHashPassword, verificarHashPassword
from src.auth.tokens import decodificarToken, generarTokenAcceso, generarTokenRefresh


# Busca un usuario por correo
def obtenerUsuarioPorEmail(baseDatos: Session, email: str) -> Usuario | None:
    return baseDatos.query(Usuario).filter(Usuario.email == email).first()


# Busca un usuario por id
def obtenerUsuarioPorId(baseDatos: Session, userId: UUID) -> Usuario | None:
    return baseDatos.query(Usuario).filter(Usuario.id == userId).first()


# Registra un usuario con password protegida y llaves generadas
def registrarUsuario(
    baseDatos: Session, displayName: str, email: str, password: str
) -> Usuario:
    passwordHash = generarHashPassword(password)
    publicKey, privateKeyPem = generarParLlavesUsuario()
    encryptedPrivateKey = cifrarLlavePrivada(password, privateKeyPem)

    usuarioNuevo = Usuario(
        email=email.strip().lower(),
        displayName=displayName.strip(),
        passwordHash=passwordHash,
        publicKey=publicKey,
        encryptedPrivateKey=encryptedPrivateKey,
        totpSecret=None,
    )

    baseDatos.add(usuarioNuevo)
    baseDatos.commit()
    baseDatos.refresh(usuarioNuevo)

    return usuarioNuevo


# Autentica al usuario con correo y contrasena
def autenticarUsuario(baseDatos: Session, email: str, password: str) -> Usuario | None:
    usuario = obtenerUsuarioPorEmail(baseDatos, email.strip().lower())

    if not usuario:
        return None

    passwordValido = verificarHashPassword(password, usuario.passwordHash)

    if not passwordValido:
        return None

    return usuario


# Construye los tokens de sesion del usuario
def construirSesionUsuario(usuario: Usuario) -> dict:
    datosBase = {
        "sub": str(usuario.id),
        "email": usuario.email,
        "displayName": usuario.displayName,
    }

    accessToken = generarTokenAcceso(datosBase)
    refreshToken = generarTokenRefresh(datosBase)

    return {
        "accessToken": accessToken,
        "refreshToken": refreshToken,
        "tokenType": "bearer",
        "userId": usuario.id,
        "email": usuario.email,
        "displayName": usuario.displayName,
    }


# Procesa el login inicial considerando si MFA esta activo
def procesarLoginUsuario(baseDatos: Session, email: str, password: str) -> dict:
    usuario = autenticarUsuario(baseDatos, email, password)

    if not usuario:
        raise ValueError("Credenciales invalidas")

    mfaActiva = bool(usuario.totpSecret)

    if mfaActiva:
        return {
            "accessToken": None,
            "refreshToken": None,
            "tokenType": "bearer",
            "userId": usuario.id,
            "email": usuario.email,
            "displayName": usuario.displayName,
            "mfaActiva": True,
            "requiereMfa": True,
            "mensaje": "MFA requerido. Debe verificar el codigo TOTP para completar el inicio de sesion",
        }

    sesion = construirSesionUsuario(usuario)

    return {
        **sesion,
        "mfaActiva": False,
        "requiereMfa": False,
        "mensaje": "Inicio de sesion exitoso",
    }


# Habilita MFA para un usuario y retorna datos del QR
def habilitarMfaUsuario(baseDatos: Session, userId: UUID) -> dict:
    usuario = obtenerUsuarioPorId(baseDatos, userId)

    if not usuario:
        raise ValueError("Usuario no encontrado")

    if not usuario.totpSecret:
        usuario.totpSecret = generarSecretoTotp()
        baseDatos.commit()
        baseDatos.refresh(usuario)

    otpauthUrl = construirUrlTotp(email=usuario.email, secretoTotp=usuario.totpSecret)

    qrBase64 = generarQrBase64(otpauthUrl)

    return {
        "userId": usuario.id,
        "email": usuario.email,
        "mfaActiva": True,
        "otpauthUrl": otpauthUrl,
        "qrBase64": qrBase64,
    }


# Verifica un codigo TOTP del usuario
def verificarMfaUsuario(baseDatos: Session, email: str, codigoTotp: str) -> dict:
    usuario = obtenerUsuarioPorEmail(baseDatos, email.strip().lower())

    if not usuario:
        raise ValueError("Usuario no encontrado")

    if not usuario.totpSecret:
        raise ValueError("El usuario no tiene MFA activado")

    codigoValido = verificarCodigoTotp(usuario.totpSecret, codigoTotp)

    return {
        "email": usuario.email,
        "codigoValido": codigoValido,
        "mensaje": "Codigo TOTP valido" if codigoValido else "Codigo TOTP invalido",
    }


# Completa el login con password y TOTP y emite tokens
def completarLoginConMfa(
    baseDatos: Session, email: str, password: str, codigoTotp: str
) -> dict:
    usuario = autenticarUsuario(baseDatos, email, password)

    if not usuario:
        raise ValueError("Credenciales invalidas")

    if not usuario.totpSecret:
        raise ValueError("El usuario no tiene MFA activado")

    codigoValido = verificarCodigoTotp(usuario.totpSecret, codigoTotp)

    if not codigoValido:
        raise ValueError("Codigo TOTP invalido")

    sesion = construirSesionUsuario(usuario)

    return {**sesion, "mensaje": "Inicio de sesion con MFA exitoso"}


# Genera una nueva sesion desde refresh token
def refrescarSesionUsuario(refreshToken: str) -> dict:
    datosToken = decodificarToken(refreshToken)

    if datosToken.get("type") != "refresh":
        raise ValueError("El token proporcionado no es un refresh token valido")

    datosBase = {
        "sub": datosToken["sub"],
        "email": datosToken["email"],
        "displayName": datosToken["displayName"],
    }

    accessTokenNuevo = generarTokenAcceso(datosBase)
    refreshTokenNuevo = generarTokenRefresh(datosBase)

    return {
        "accessToken": accessTokenNuevo,
        "refreshToken": refreshTokenNuevo,
        "tokenType": "bearer",
    }
