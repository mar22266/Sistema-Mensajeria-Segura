from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.auth.baseDatos import obtenerBaseDatos
from src.auth.esquemas import LlavePublicaUsuarioSalida
from src.auth.servicio import obtenerUsuarioPorId


routerUsers = APIRouter(prefix="/users", tags=["users"])


# Retorna la llave publica PEM de un usuario
@routerUsers.get(
    "/{userId}/key",
    response_model=LlavePublicaUsuarioSalida,
    status_code=status.HTTP_200_OK,
)
def obtenerLlavePublicaUsuarioRuta(
    userId: UUID, baseDatos: Session = Depends(obtenerBaseDatos)
):
    usuario = obtenerUsuarioPorId(baseDatos, userId)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )

    return LlavePublicaUsuarioSalida(
        userId=usuario.id, email=usuario.email, publicKey=usuario.publicKey
    )
