from src.auth.baseDatos import SesionLocal
from src.crypto.modelos import Grupo, GrupoMiembro, Mensaje, MensajeDestinatario


# Verifica envio y recuperacion de mensaje individual cifrado
def testEnviarYRecuperarMensajeIndividual(cliente, usuariosPrueba):
    senderId = usuariosPrueba["a"]["id"]
    destId = usuariosPrueba["b"]["id"]

    respuestaEnvio = cliente.post(
        f"/messages/{destId}",
        json={"senderId": senderId, "plaintext": "Hola mensaje individual cifrado"},
    )

    assert respuestaEnvio.status_code == 201

    cuerpoEnvio = respuestaEnvio.json()

    assert cuerpoEnvio["senderId"] == senderId
    assert cuerpoEnvio["recipientId"] == destId
    assert cuerpoEnvio["groupId"] is None
    assert cuerpoEnvio["ciphertext"] != "Hola mensaje individual cifrado"
    assert cuerpoEnvio["encryptedKey"] != ""
    assert cuerpoEnvio["nonce"] != ""
    assert cuerpoEnvio["authTag"] != ""

    respuestaRecuperacion = cliente.get(f"/messages/{destId}?password=ClaveSegura123")

    assert respuestaRecuperacion.status_code == 200

    cuerpoRecuperacion = respuestaRecuperacion.json()

    assert cuerpoRecuperacion["userId"] == destId
    assert len(cuerpoRecuperacion["mensajes"]) == 1
    assert (
        cuerpoRecuperacion["mensajes"][0]["plaintext"]
        == "Hola mensaje individual cifrado"
    )


# Verifica creacion de grupo y miembros
def testCrearGrupo(cliente, usuariosPrueba):
    creadoPor = usuariosPrueba["a"]["id"]
    miembroB = usuariosPrueba["b"]["id"]
    miembroC = usuariosPrueba["c"]["id"]

    respuesta = cliente.post(
        "/groups",
        json={
            "nombre": "Grupo Prueba",
            "creadoPor": creadoPor,
            "miembrosIds": [miembroB, miembroC],
        },
    )

    assert respuesta.status_code == 201

    cuerpo = respuesta.json()

    assert cuerpo["nombre"] == "Grupo Prueba"
    assert cuerpo["creadoPor"] == creadoPor
    assert len(cuerpo["miembrosIds"]) == 3

    sesion = SesionLocal()
    try:
        grupo = sesion.query(Grupo).filter(Grupo.id == cuerpo["groupId"]).first()
        miembros = (
            sesion.query(GrupoMiembro)
            .filter(GrupoMiembro.groupId == cuerpo["groupId"])
            .all()
        )

        assert grupo is not None
        assert len(miembros) == 3
    finally:
        sesion.close()


# Verifica envio y recuperacion de mensaje grupal cifrado
def testEnviarYRecuperarMensajeGrupal(cliente, usuariosPrueba):
    creadoPor = usuariosPrueba["a"]["id"]
    miembroB = usuariosPrueba["b"]["id"]
    miembroC = usuariosPrueba["c"]["id"]

    respuestaGrupo = cliente.post(
        "/groups",
        json={
            "nombre": "Grupo A",
            "creadoPor": creadoPor,
            "miembrosIds": [miembroB, miembroC],
        },
    )

    assert respuestaGrupo.status_code == 201

    groupId = respuestaGrupo.json()["groupId"]

    respuestaEnvio = cliente.post(
        f"/groups/{groupId}/messages",
        json={"senderId": miembroB, "plaintext": "Hola grupo este mensaje es cifrado"},
    )

    assert respuestaEnvio.status_code == 201

    cuerpoEnvio = respuestaEnvio.json()

    assert cuerpoEnvio["groupId"] == groupId
    assert cuerpoEnvio["encryptedKeysGeneradas"] == 3
    assert cuerpoEnvio["ciphertext"] != "Hola grupo este mensaje es cifrado"
    assert cuerpoEnvio["nonce"] != ""
    assert cuerpoEnvio["authTag"] != ""

    sesion = SesionLocal()
    try:
        mensaje = (
            sesion.query(Mensaje).filter(Mensaje.id == cuerpoEnvio["messageId"]).first()
        )
        clavesPorMiembro = (
            sesion.query(MensajeDestinatario)
            .filter(MensajeDestinatario.messageId == cuerpoEnvio["messageId"])
            .all()
        )

        assert mensaje is not None
        assert mensaje.recipientId is None
        assert mensaje.groupId is not None
        assert mensaje.encryptedKey is None
        assert len(clavesPorMiembro) == 3
    finally:
        sesion.close()

    respuestaRecuperacion = cliente.get(f"/messages/{miembroC}?password=ClaveSegura123")
    assert respuestaRecuperacion.status_code == 200
    cuerpoRecuperacion = respuestaRecuperacion.json()
    assert len(cuerpoRecuperacion["mensajes"]) == 1
    assert cuerpoRecuperacion["mensajes"][0]["groupId"] == groupId
    assert (
        cuerpoRecuperacion["mensajes"][0]["plaintext"]
        == "Hola grupo este mensaje es cifrado"
    )


# Verifica error al recuperar mensajes con password incorrecta
def testRecuperarMensajesConPasswordIncorrecta(cliente, usuariosPrueba):
    senderId = usuariosPrueba["a"]["id"]
    destId = usuariosPrueba["b"]["id"]
    cliente.post(
        f"/messages/{destId}",
        json={"senderId": senderId, "plaintext": "Mensaje protegido"},
    )

    respuesta = cliente.get(f"/messages/{destId}?password=ClaveIncorrecta999")
    assert respuesta.status_code == 400
    assert (
        respuesta.json()["detail"]
        == "No fue posible descifrar los mensajes con los datos proporcionados"
    )


# Verifica error al enviar mensaje a usuario inexistente
def testEnviarMensajeAUsuarioInexistente(cliente, usuariosPrueba, uuidInexistente):
    senderId = usuariosPrueba["a"]["id"]

    respuesta = cliente.post(
        f"/messages/{uuidInexistente}",
        json={"senderId": senderId, "plaintext": "Mensaje a destino inexistente"},
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Remitente o destinatario no encontrado"
