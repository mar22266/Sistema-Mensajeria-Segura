from sqlalchemy.orm import Session

from src.auth.criptografia import cifrarLlavePrivada, generarParLlavesUsuario
from src.auth.modelos import Usuario
from src.auth.seguridad import generarHashPassword, verificarHashPassword


# Busca un usuario por correo
def obtenerUsuarioPorEmail(baseDatos: Session, email: str) -> Usuario | None:
    return baseDatos.query(Usuario).filter(Usuario.email == email).first()


# Registra un usuario con password protegida y llaves generadas
def registrarUsuario(
    baseDatos: Session, displayName: str, email: str, password: str
) -> Usuario:
    passwordHash = generarHashPassword(password)
    publicKey, privateKeyPem = generarParLlavesUsuario()
    encryptedPrivateKey = cifrarLlavePrivada(password, privateKeyPem)

    usuarioNuevo = Usuario(
        email=email,
        displayName=displayName,
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
    usuario = obtenerUsuarioPorEmail(baseDatos, email)

    if not usuario:
        return None

    passwordValido = verificarHashPassword(password, usuario.passwordHash)

    if not passwordValido:
        return None

    return usuario
