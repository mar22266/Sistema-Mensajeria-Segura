from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from src.auth.baseDatos import obtenerBaseDatos
from src.auth.dependencias import obtenerUsuarioActual
from src.auth.modelos import Usuario
from src.contacts.esquemas import (
    ActualizarContactoEntrada,
    ContactoSalida,
    CrearContactoEntrada,
)
from src.contacts.servicio import (
    actualizarContacto,
    crearContacto,
    eliminarContacto,
    obtenerContactoUsuario,
    obtenerContactosUsuario,
)


routerContacts = APIRouter(prefix="/contacts", tags=["contacts"])


# Crea un contacto para el usuario autenticado
@routerContacts.post(
    "", response_model=ContactoSalida, status_code=status.HTTP_201_CREATED
)
def crearContactoRuta(
    datosEntrada: CrearContactoEntrada,
    usuarioActual: Usuario = Depends(obtenerUsuarioActual),
    baseDatos: Session = Depends(obtenerBaseDatos),
):
    return crearContacto(
        baseDatos=baseDatos,
        ownerId=usuarioActual.id,
        nombre=datosEntrada.nombre,
        email=str(datosEntrada.email),
    )


# Retorna los contactos del usuario autenticado
@routerContacts.get("", response_model=list[ContactoSalida], status_code=status.HTTP_200_OK)
def obtenerContactosRuta(
    usuarioActual: Usuario = Depends(obtenerUsuarioActual),
    baseDatos: Session = Depends(obtenerBaseDatos),
):
    return obtenerContactosUsuario(baseDatos=baseDatos, ownerId=usuarioActual.id)


# Retorna un contacto del usuario autenticado
@routerContacts.get(
    "/{contactId}", response_model=ContactoSalida, status_code=status.HTTP_200_OK
)
def obtenerContactoRuta(
    contactId: UUID,
    usuarioActual: Usuario = Depends(obtenerUsuarioActual),
    baseDatos: Session = Depends(obtenerBaseDatos),
):
    contacto = obtenerContactoUsuario(baseDatos, contactId, usuarioActual.id)

    if not contacto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contacto no encontrado"
        )

    return contacto


# Actualiza un contacto del usuario autenticado
@routerContacts.put(
    "/{contactId}", response_model=ContactoSalida, status_code=status.HTTP_200_OK
)
def actualizarContactoRuta(
    contactId: UUID,
    datosEntrada: ActualizarContactoEntrada,
    usuarioActual: Usuario = Depends(obtenerUsuarioActual),
    baseDatos: Session = Depends(obtenerBaseDatos),
):
    contacto = obtenerContactoUsuario(baseDatos, contactId, usuarioActual.id)

    if not contacto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contacto no encontrado"
        )

    return actualizarContacto(
        baseDatos=baseDatos,
        contacto=contacto,
        nombre=datosEntrada.nombre,
        email=str(datosEntrada.email),
    )


# Elimina un contacto del usuario autenticado
@routerContacts.delete("/{contactId}", status_code=status.HTTP_204_NO_CONTENT)
def eliminarContactoRuta(
    contactId: UUID,
    usuarioActual: Usuario = Depends(obtenerUsuarioActual),
    baseDatos: Session = Depends(obtenerBaseDatos),
):
    contacto = obtenerContactoUsuario(baseDatos, contactId, usuarioActual.id)

    if not contacto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contacto no encontrado"
        )

    eliminarContacto(baseDatos, contacto)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
