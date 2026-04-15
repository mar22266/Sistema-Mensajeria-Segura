# Verifica obtencion correcta de llave publica
def testObtenerLlavePublicaUsuario(cliente, usuarioRegistrado):
    userId = usuarioRegistrado["datos"]["id"]
    respuesta = cliente.get(f"/users/{userId}/key")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["userId"] == userId
    assert cuerpo["email"] == "andre@correo.com"
    assert cuerpo["publicKey"].startswith("-----BEGIN PUBLIC KEY-----")
    assert cuerpo["publicKey"].endswith("-----END PUBLIC KEY-----\n") or cuerpo[
        "publicKey"
    ].endswith("-----END PUBLIC KEY-----")


# Verifica error cuando el usuario no existe
def testObtenerLlavePublicaUsuarioInexistente(cliente, uuidInexistente):
    respuesta = cliente.get(f"/users/{uuidInexistente}/key")
    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Usuario no encontrado"


# Verifica que la llave publica no venga vacia
def testObtenerLlavePublicaNoVacia(cliente, usuarioRegistrado):
    userId = usuarioRegistrado["datos"]["id"]
    respuesta = cliente.get(f"/users/{userId}/key")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["publicKey"] is not None
    assert cuerpo["publicKey"] != ""
    assert len(cuerpo["publicKey"]) > 50


# Verifica que el correo retornado corresponde al usuario registrado
def testObtenerLlavePublicaRetornaCorreoCorrecto(cliente, usuarioRegistrado):
    userId = usuarioRegistrado["datos"]["id"]
    respuesta = cliente.get(f"/users/{userId}/key")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["email"] == usuarioRegistrado["datos"]["email"]


# Verifica que el userId retornado corresponde al solicitado
def testObtenerLlavePublicaRetornaUserIdCorrecto(cliente, usuarioRegistrado):
    userId = usuarioRegistrado["datos"]["id"]
    respuesta = cliente.get(f"/users/{userId}/key")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["userId"] == userId


# Verifica que el formato PEM de la llave publica sea valido
def testObtenerLlavePublicaFormatoPemValido(cliente, usuarioRegistrado):
    userId = usuarioRegistrado["datos"]["id"]
    respuesta = cliente.get(f"/users/{userId}/key")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    llavePublica = cuerpo["publicKey"]
    assert "-----BEGIN PUBLIC KEY-----" in llavePublica
    assert "-----END PUBLIC KEY-----" in llavePublica


# Verifica que una peticion con uuid invalido no sea aceptada
def testObtenerLlavePublicaConUuidInvalido(cliente):
    respuesta = cliente.get("/users/no-es-un-uuid/key")
    assert respuesta.status_code in [400, 422]


# Verifica que distintos usuarios tengan llaves publicas distintas
def testObtenerLlavesPublicasDiferentesPorUsuario(cliente):
    respuestaUno = cliente.post(
        "/auth/register",
        json={
            "displayName": "Andre",
            "email": "andre1@correo.com",
            "password": "PasswordSegura123",
        },
    )

    respuestaDos = cliente.post(
        "/auth/register",
        json={
            "displayName": "Carlos",
            "email": "carlos1@correo.com",
            "password": "PasswordSegura123",
        },
    )
    assert respuestaUno.status_code == 201
    assert respuestaDos.status_code == 201
    userIdUno = respuestaUno.json()["id"]
    userIdDos = respuestaDos.json()["id"]
    llaveUno = cliente.get(f"/users/{userIdUno}/key")
    llaveDos = cliente.get(f"/users/{userIdDos}/key")
    assert llaveUno.status_code == 200
    assert llaveDos.status_code == 200
    publicKeyUno = llaveUno.json()["publicKey"]
    publicKeyDos = llaveDos.json()["publicKey"]
    assert publicKeyUno != publicKeyDos
