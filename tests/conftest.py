import uuid

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.auth.baseDatos import SesionLocal
from src.auth.modelos import Usuario


# Limpia la tabla de usuarios antes de cada prueba
@pytest.fixture(autouse=True)
def limpiarBaseDatos():
    sesion = SesionLocal()
    try:
        sesion.query(Usuario).delete()
        sesion.commit()
        yield
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
    return {"respuesta": respuesta, "datos": cuerpo, "credenciales": datosUsuario}


# Genera un uuid inexistente para pruebas negativas
@pytest.fixture
def uuidInexistente():
    return str(uuid.uuid4())
