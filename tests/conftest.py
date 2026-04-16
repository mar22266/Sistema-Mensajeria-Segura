import uuid

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.auth.baseDatos import SesionLocal
from src.auth.modelos import Usuario
from src.blockchain.modelos import BloqueBlockchain
from src.crypto.modelos import Grupo, GrupoMiembro, Mensaje, MensajeDestinatario


# Limpia la base de datos antes y despues de cada prueba
@pytest.fixture(autouse=True)
def limpiarBaseDatos():
    sesion = SesionLocal()
    try:
        sesion.query(MensajeDestinatario).delete()
        sesion.query(Mensaje).delete()
        sesion.query(GrupoMiembro).delete()
        sesion.query(Grupo).delete()
        sesion.query(BloqueBlockchain).delete()
        sesion.query(Usuario).delete()
        sesion.commit()

        yield

        sesion.query(MensajeDestinatario).delete()
        sesion.query(Mensaje).delete()
        sesion.query(GrupoMiembro).delete()
        sesion.query(Grupo).delete()
        sesion.query(BloqueBlockchain).delete()
        sesion.query(Usuario).delete()
        sesion.commit()
    finally:
        sesion.close()


# Retorna un cliente de pruebas para la API
@pytest.fixture
def cliente():
    with TestClient(app) as clientePrueba:
        yield clientePrueba


# Crea un usuario de prueba desde el endpoint real
@pytest.fixture
def usuarioRegistrado(cliente):
    datosUsuario = {
        "displayName": "Andre",
        "email": "andre@correo.com",
        "password": "ClaveSegura123",
    }

    respuesta = cliente.post("/auth/register", json=datosUsuario)
    cuerpo = respuesta.json()

    return {
        "respuesta": respuesta,
        "datos": cuerpo,
        "credenciales": datosUsuario,
    }


# Genera un uuid inexistente para pruebas negativas
@pytest.fixture
def uuidInexistente():
    return str(uuid.uuid4())


# Registra un usuario generico desde el endpoint real
def registrarUsuario(cliente, displayName, email, password):
    respuesta = cliente.post(
        "/auth/register",
        json={
            "displayName": displayName,
            "email": email,
            "password": password,
        },
    )
    return respuesta.json()


# Crea tres usuarios para pruebas del modulo 2 y 3
@pytest.fixture
def usuariosPrueba(cliente):
    usuarioA = registrarUsuario(cliente, "Usuario A", "a@correo.com", "ClaveSegura123")
    usuarioB = registrarUsuario(cliente, "Usuario B", "b@correo.com", "ClaveSegura123")
    usuarioC = registrarUsuario(cliente, "Usuario C", "c@correo.com", "ClaveSegura123")

    return {
        "a": usuarioA,
        "b": usuarioB,
        "c": usuarioC,
    }
