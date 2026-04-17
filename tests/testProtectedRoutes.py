from tests.conftest import generarCodigoTotp


# Obtiene un access token normal o con mfa
def obtenerAccessToken(cliente, email, password, activarMfa=False, userId=""):
    loginRespuesta = cliente.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert loginRespuesta.status_code == 200
    loginData = loginRespuesta.json()

    if not activarMfa:
        return loginData["accessToken"]

    accessTokenTemporal = loginData["accessToken"]

    cliente.post(
        "/auth/mfa/enable",
        json={
            "userId": userId,
        },
        headers={"Authorization": f"Bearer {accessTokenTemporal}"},
    )

    codigoTotp = generarCodigoTotp(email)

    loginMfaRespuesta = cliente.post(
        "/auth/mfa/login",
        json={
            "email": email,
            "password": password,
            "codigoTotp": codigoTotp,
        },
    )

    assert loginMfaRespuesta.status_code == 200
    return loginMfaRespuesta.json()["accessToken"]


# Verifica acceso protegido a recuperar mensajes propios
def testEndpointProtegidoDebePermitirRecuperarMensajesPropios(cliente, usuariosPrueba):
    accessToken = obtenerAccessToken(cliente, "a@correo.com", "ClaveSegura123")

    cliente.post(
        f"/messages/{usuariosPrueba['b']['id']}",
        json={
            "senderId": usuariosPrueba["a"]["id"],
            "senderPassword": "ClaveSegura123",
            "plaintext": "Mensaje protegido para ruta autenticada",
        },
        headers={"Authorization": f"Bearer {accessToken}"},
    )

    accessTokenB = obtenerAccessToken(cliente, "b@correo.com", "ClaveSegura123")

    respuesta = cliente.get(
        f"/messages/{usuariosPrueba['b']['id']}?password=ClaveSegura123",
        headers={"Authorization": f"Bearer {accessTokenB}"},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["userId"] == usuariosPrueba["b"]["id"]


# Verifica que no se pueda recuperar mensajes de otro usuario
def testEndpointProtegidoDebeRechazarMensajesDeOtroUsuario(cliente, usuariosPrueba):
    accessTokenA = obtenerAccessToken(cliente, "a@correo.com", "ClaveSegura123")

    respuesta = cliente.get(
        f"/messages/{usuariosPrueba['b']['id']}?password=ClaveSegura123",
        headers={"Authorization": f"Bearer {accessTokenA}"},
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == "No puede recuperar mensajes de otro usuario"


# Verifica que no se pueda enviar mensaje en nombre de otro usuario
def testEndpointProtegidoDebeRechazarEnvioEnNombreDeOtro(cliente, usuariosPrueba):
    accessTokenA = obtenerAccessToken(cliente, "a@correo.com", "ClaveSegura123")

    respuesta = cliente.post(
        f"/messages/{usuariosPrueba['c']['id']}",
        json={
            "senderId": usuariosPrueba["b"]["id"],
            "senderPassword": "ClaveSegura123",
            "plaintext": "Intento invalido",
        },
        headers={"Authorization": f"Bearer {accessTokenA}"},
    )

    assert respuesta.status_code == 403
    assert (
        respuesta.json()["detail"]
        == "No puede enviar mensajes en nombre de otro usuario"
    )


# Verifica que no se pueda crear grupo en nombre de otro usuario
def testEndpointProtegidoDebeRechazarCrearGrupoEnNombreDeOtro(cliente, usuariosPrueba):
    accessTokenA = obtenerAccessToken(cliente, "a@correo.com", "ClaveSegura123")

    respuesta = cliente.post(
        "/groups",
        json={
            "nombre": "Grupo invalido",
            "creadoPor": usuariosPrueba["b"]["id"],
            "miembrosIds": [usuariosPrueba["c"]["id"]],
        },
        headers={"Authorization": f"Bearer {accessTokenA}"},
    )

    assert respuesta.status_code == 403
    assert (
        respuesta.json()["detail"]
        == "No puede crear un grupo en nombre de otro usuario"
    )


# Verifica flujo completo end to end con mfa, mensaje y blockchain
def testFlujoCompletoEndToEndConMfa(cliente, usuariosPrueba):
    accessTokenA = obtenerAccessToken(
        cliente,
        "a@correo.com",
        "ClaveSegura123",
        activarMfa=True,
        userId=usuariosPrueba["a"]["id"],
    )

    respuestaEnvio = cliente.post(
        f"/messages/{usuariosPrueba['b']['id']}",
        json={
            "senderId": usuariosPrueba["a"]["id"],
            "senderPassword": "ClaveSegura123",
            "plaintext": "Flujo final con mfa cifrado firma y blockchain",
        },
        headers={"Authorization": f"Bearer {accessTokenA}"},
    )

    assert respuestaEnvio.status_code == 201

    accessTokenB = obtenerAccessToken(cliente, "b@correo.com", "ClaveSegura123")

    respuestaRecuperacion = cliente.get(
        f"/messages/{usuariosPrueba['b']['id']}?password=ClaveSegura123",
        headers={"Authorization": f"Bearer {accessTokenB}"},
    )

    assert respuestaRecuperacion.status_code == 200

    cuerpo = respuestaRecuperacion.json()

    assert len(cuerpo["mensajes"]) == 1
    assert (
        cuerpo["mensajes"][0]["plaintext"]
        == "Flujo final con mfa cifrado firma y blockchain"
    )
    assert cuerpo["mensajes"][0]["firmaVerificada"] is True
    assert cuerpo["mensajes"][0]["estadoFirma"] == "VERIFICADO"

    respuestaBlockchain = cliente.get("/blockchain/verify")

    assert respuestaBlockchain.status_code == 200
    assert respuestaBlockchain.json()["esValida"] is True
