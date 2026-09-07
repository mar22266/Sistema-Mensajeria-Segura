# Obtiene un token de acceso mediante el login existente
def obtenerAccessToken(cliente, email, password):
    respuesta = cliente.post(
        "/auth/login", json={"email": email, "password": password}
    )
    assert respuesta.status_code == 200
    return respuesta.json()["accessToken"]


# Crea un contacto usando el endpoint protegido
def crearContacto(cliente, token, nombre="Ana Lopez", email="ana@correo.com"):
    return cliente.post(
        "/contacts",
        json={"nombre": nombre, "email": email},
        headers={"Authorization": f"Bearer {token}"},
    )


# Verifica creacion de contacto para el usuario autenticado
def testCrearContactoAutenticado(cliente, usuarioRegistrado):
    token = obtenerAccessToken(cliente, "andre@correo.com", "ClaveSegura123")

    respuesta = crearContacto(cliente, token)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["nombre"] == "Ana Lopez"
    assert cuerpo["email"] == "ana@correo.com"
    assert cuerpo["ownerId"] == usuarioRegistrado["datos"]["id"]
    assert "id" in cuerpo
    assert "createdAt" in cuerpo


# Verifica que el listado contiene solo contactos del usuario autenticado
def testListarContactosDelUsuarioAutenticado(cliente, usuarioRegistrado):
    token = obtenerAccessToken(cliente, "andre@correo.com", "ClaveSegura123")
    crearContacto(cliente, token, "Ana Lopez", "ana@correo.com")
    crearContacto(cliente, token, "Luis Perez", "luis@correo.com")

    respuesta = cliente.get("/contacts", headers={"Authorization": f"Bearer {token}"})

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 2
    assert {contacto["nombre"] for contacto in respuesta.json()} == {
        "Ana Lopez",
        "Luis Perez",
    }


# Verifica consulta de un contacto propio
def testObtenerContactoPropio(cliente, usuarioRegistrado):
    token = obtenerAccessToken(cliente, "andre@correo.com", "ClaveSegura123")
    contacto = crearContacto(cliente, token).json()

    respuesta = cliente.get(
        f"/contacts/{contacto['id']}", headers={"Authorization": f"Bearer {token}"}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["id"] == contacto["id"]


# Verifica actualizacion de un contacto propio
def testActualizarContactoPropio(cliente, usuarioRegistrado):
    token = obtenerAccessToken(cliente, "andre@correo.com", "ClaveSegura123")
    contacto = crearContacto(cliente, token).json()

    respuesta = cliente.put(
        f"/contacts/{contacto['id']}",
        json={"nombre": "Ana Maria Lopez", "email": "ana.maria@correo.com"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Ana Maria Lopez"
    assert respuesta.json()["email"] == "ana.maria@correo.com"


# Verifica eliminacion de un contacto propio
def testEliminarContactoPropio(cliente, usuarioRegistrado):
    token = obtenerAccessToken(cliente, "andre@correo.com", "ClaveSegura123")
    contacto = crearContacto(cliente, token).json()

    respuesta = cliente.delete(
        f"/contacts/{contacto['id']}", headers={"Authorization": f"Bearer {token}"}
    )

    assert respuesta.status_code == 204
    consulta = cliente.get(
        f"/contacts/{contacto['id']}", headers={"Authorization": f"Bearer {token}"}
    )
    assert consulta.status_code == 404


# Verifica que no se permita usar el CRUD sin JWT
def testContactosRechazanPeticionSinJwt(cliente):
    respuesta = cliente.get("/contacts")

    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == "Se requiere token de acceso"


# Verifica que otro usuario no pueda consultar, modificar ni eliminar contactos ajenos
def testUsuarioNoPuedeAccederContactoDeOtroUsuario(cliente, usuariosPrueba):
    tokenA = obtenerAccessToken(cliente, "a@correo.com", "ClaveSegura123")
    tokenB = obtenerAccessToken(cliente, "b@correo.com", "ClaveSegura123")
    contacto = crearContacto(cliente, tokenA).json()
    headersB = {"Authorization": f"Bearer {tokenB}"}

    consulta = cliente.get(f"/contacts/{contacto['id']}", headers=headersB)
    actualizacion = cliente.put(
        f"/contacts/{contacto['id']}",
        json={"nombre": "Intento invalido", "email": "invalido@correo.com"},
        headers=headersB,
    )
    eliminacion = cliente.delete(f"/contacts/{contacto['id']}", headers=headersB)

    assert consulta.status_code == 404
    assert actualizacion.status_code == 404
    assert eliminacion.status_code == 404
    assert consulta.json()["detail"] == "Contacto no encontrado"
