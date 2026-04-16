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
