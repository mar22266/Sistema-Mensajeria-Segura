from uuid import UUID

from sqlalchemy.orm import Session

from src.contacts.modelos import Contacto


# Crea un contacto asociado al usuario autenticado
def crearContacto(baseDatos: Session, ownerId: UUID, nombre: str, email: str) -> Contacto:
    contacto = Contacto(ownerId=ownerId, nombre=nombre, email=email)
    baseDatos.add(contacto)
    baseDatos.commit()
    baseDatos.refresh(contacto)
    return contacto


# Obtiene solamente los contactos de un usuario
def obtenerContactosUsuario(baseDatos: Session, ownerId: UUID) -> list[Contacto]:
    return (
        baseDatos.query(Contacto)
        .filter(Contacto.ownerId == ownerId)
        .order_by(Contacto.createdAt.desc())
        .all()
    )


# Obtiene un contacto solo si pertenece al usuario indicado
def obtenerContactoUsuario(
    baseDatos: Session, contactoId: UUID, ownerId: UUID
) -> Contacto | None:
    return (
        baseDatos.query(Contacto)
        .filter(Contacto.id == contactoId, Contacto.ownerId == ownerId)
        .first()
    )


# Actualiza los datos de un contacto del usuario
def actualizarContacto(
    baseDatos: Session, contacto: Contacto, nombre: str, email: str
) -> Contacto:
    contacto.nombre = nombre
    contacto.email = email
    baseDatos.commit()
    baseDatos.refresh(contacto)
    return contacto


# Elimina un contacto del usuario
def eliminarContacto(baseDatos: Session, contacto: Contacto) -> None:
    baseDatos.delete(contacto)
    baseDatos.commit()
