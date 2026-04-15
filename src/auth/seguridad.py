from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

hasheadorPassword = PasswordHasher()


# Genera el hash seguro de una contrasena
def generarHashPassword(passwordPlano: str) -> str:
    return hasheadorPassword.hash(passwordPlano)


# Verifica si la contrasena coincide con el hash
def verificarHashPassword(passwordPlano: str, passwordHash: str) -> bool:
    try:
        return hasheadorPassword.verify(passwordHash, passwordPlano)
    except VerifyMismatchError:
        return False
