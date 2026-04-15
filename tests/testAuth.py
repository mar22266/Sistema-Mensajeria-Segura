from src.auth.baseDatos import SesionLocal
from src.auth.modelos import Usuario


# Verifica registro correcto de usuario
def testRegistrarUsuarioExitosamente(cliente):
    datos = {
        "displayName": "Andre",
        "email": "andre@correo.com",
        "password": "ClaveSegura123",
    }

    respuesta = cliente.post("/auth/register", json=datos)
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert "id" in cuerpo
    assert cuerpo["email"] == "andre@correo.com"
    assert cuerpo["displayName"] == "Andre"
    assert "createdAt" in cuerpo
    sesion = SesionLocal()
    try:
        usuario = (
            sesion.query(Usuario).filter(Usuario.email == "andre@correo.com").first()
        )

        assert usuario is not None
        assert usuario.passwordHash.startswith("$argon2id$")
        assert usuario.publicKey.startswith("-----BEGIN PUBLIC KEY-----")
        assert "textoCifrado" in usuario.encryptedPrivateKey
        assert "BEGIN PRIVATE KEY" not in usuario.encryptedPrivateKey
    finally:
        sesion.close()


# Verifica que no se permita registrar un correo duplicado
def testRegistrarUsuarioDuplicado(cliente, usuarioRegistrado):
    datos = {
        "displayName": "Andre Duplicado",
        "email": "andre@correo.com",
        "password": "OtraClave123",
    }

    respuesta = cliente.post("/auth/register", json=datos)
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "El correo ya se encuentra registrado"


# Verifica login correcto con emision de jwt
def testLoginExitoso(cliente, usuarioRegistrado):
    datosLogin = {"email": "andre@correo.com", "password": "ClaveSegura123"}
    respuesta = cliente.post("/auth/login", json=datosLogin)
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert "accessToken" in cuerpo
    assert cuerpo["tokenType"] == "bearer"
    assert cuerpo["email"] == "andre@correo.com"
    assert cuerpo["displayName"] == "Andre"
    assert cuerpo["userId"] == usuarioRegistrado["datos"]["id"]


# Verifica login fallido por contrasena incorrecta
def testLoginConPasswordIncorrecta(cliente, usuarioRegistrado):
    datosLogin = {"email": "andre@correo.com", "password": "ClaveIncorrecta999"}
    respuesta = cliente.post("/auth/login", json=datosLogin)
    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == "Credenciales invalidas"


# Verifica login fallido por correo inexistente
def testLoginConCorreoInexistente(cliente):
    datosLogin = {"email": "noexiste@correo.com", "password": "ClaveSegura123"}
    respuesta = cliente.post("/auth/login", json=datosLogin)
    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == "Credenciales invalidas"
