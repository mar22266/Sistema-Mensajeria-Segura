from sqlalchemy.orm import Session

from src.auth.criptografia import cifrarLlavePrivada, generarParLlavesUsuario
from src.auth.modelos import Usuario
from src.auth.seguridad import generarHashPassword


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
