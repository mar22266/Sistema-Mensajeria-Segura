from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.auth.baseDatos import obtenerBaseDatos
from src.blockchain.esquemas import BloqueBlockchainSalida, VerificacionBlockchainSalida
from src.blockchain.servicio import (
    obtenerCadenaBlockchain,
    verificarIntegridadBlockchain,
)


routerBlockchain = APIRouter(prefix="/blockchain", tags=["blockchain"])


# Retorna la cadena completa de bloques
@routerBlockchain.get(
    "", response_model=list[BloqueBlockchainSalida], status_code=status.HTTP_200_OK
)
def obtenerBlockchainRuta(baseDatos: Session = Depends(obtenerBaseDatos)):
    bloques = obtenerCadenaBlockchain(baseDatos)
    return bloques


# Verifica la integridad completa de la cadena
@routerBlockchain.get(
    "/verify",
    response_model=VerificacionBlockchainSalida,
    status_code=status.HTTP_200_OK,
)
def verificarBlockchainRuta(baseDatos: Session = Depends(obtenerBaseDatos)):
    esValida, detalle, cantidadBloques = verificarIntegridadBlockchain(baseDatos)

    return VerificacionBlockchainSalida(
        esValida=esValida, cantidadBloques=cantidadBloques, detalle=detalle
    )
