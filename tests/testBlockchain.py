from src.auth.baseDatos import SesionLocal
from src.blockchain.modelos import BloqueBlockchain
from src.crypto.modelos import Mensaje, MensajeDestinatario


# Obtiene access token para un usuario
def obtenerAccessToken(cliente, email, password):
    respuesta = cliente.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert respuesta.status_code == 200
    return respuesta.json()["accessToken"]


# Crea un grupo de prueba y retorna su id
def crearGrupoPrueba(cliente, usuariosPrueba):
    accessTokenA = obtenerAccessToken(cliente, "a@correo.com", "ClaveSegura123")

    respuesta = cliente.post(
        "/groups",
        json={
            "nombre": "Grupo A",
            "creadoPor": usuariosPrueba["a"]["id"],
            "miembrosIds": [
                usuariosPrueba["b"]["id"],
                usuariosPrueba["c"]["id"],
            ],
        },
        headers={"Authorization": f"Bearer {accessTokenA}"},
    )

    assert respuesta.status_code == 201
    return respuesta.json()["groupId"]


# Verifica que exista el bloque genesis al consultar la cadena
def testBlockchainDebeCrearBloqueGenesis(cliente):
    respuesta = cliente.get("/blockchain")

    assert respuesta.status_code == 200

    cuerpo = respuesta.json()

    assert len(cuerpo) == 1
    assert cuerpo[0]["indice"] == 0
    assert cuerpo[0]["messageHash"] == "GENESIS"
    assert cuerpo[0]["previousHash"] == "0" * 64


# Verifica envio individual firmado y registro automatico en blockchain
def testEnviarMensajeIndividualFirmadoGeneraFirmaYBloque(cliente, usuariosPrueba):
    accessTokenA = obtenerAccessToken(cliente, "a@correo.com", "ClaveSegura123")

    respuesta = cliente.post(
        f"/messages/{usuariosPrueba['b']['id']}",
        json={
            "senderId": usuariosPrueba["a"]["id"],
            "senderPassword": "ClaveSegura123",
            "plaintext": "Mensaje individual firmado para blockchain",
        },
        headers={"Authorization": f"Bearer {accessTokenA}"},
    )

    assert respuesta.status_code == 201

    cuerpo = respuesta.json()

    assert cuerpo["senderId"] == usuariosPrueba["a"]["id"]
    assert cuerpo["recipientId"] == usuariosPrueba["b"]["id"]
    assert cuerpo["groupId"] is None
    assert cuerpo["signature"] is not None
    assert cuerpo["signature"] != ""

    sesion = SesionLocal()
    try:
        mensaje = (
            sesion.query(Mensaje).filter(Mensaje.id == cuerpo["messageId"]).first()
        )
        bloques = (
            sesion.query(BloqueBlockchain).order_by(BloqueBlockchain.indice.asc()).all()
        )

        assert mensaje is not None
        assert mensaje.signature is not None
        assert len(bloques) == 2
        assert bloques[0].indice == 0
        assert bloques[1].indice == 1
        assert bloques[1].senderId == usuariosPrueba["a"]["id"]
        assert bloques[1].recipientId == usuariosPrueba["b"]["id"]
        assert bloques[1].previousHash == bloques[0].hashActual
    finally:
        sesion.close()


# Verifica recuperacion de mensaje con firma valida
def testRecuperarMensajeDebeVerificarFirmaValida(cliente, usuariosPrueba):
    accessTokenA = obtenerAccessToken(cliente, "a@correo.com", "ClaveSegura123")
    accessTokenB = obtenerAccessToken(cliente, "b@correo.com", "ClaveSegura123")

    respuestaEnvio = cliente.post(
        f"/messages/{usuariosPrueba['b']['id']}",
        json={
            "senderId": usuariosPrueba["a"]["id"],
            "senderPassword": "ClaveSegura123",
            "plaintext": "Mensaje con firma valida",
        },
        headers={"Authorization": f"Bearer {accessTokenA}"},
    )

    assert respuestaEnvio.status_code == 201

    respuestaRecuperacion = cliente.get(
        f"/messages/{usuariosPrueba['b']['id']}?password=ClaveSegura123",
        headers={"Authorization": f"Bearer {accessTokenB}"},
    )

    assert respuestaRecuperacion.status_code == 200

    cuerpo = respuestaRecuperacion.json()

    assert cuerpo["userId"] == usuariosPrueba["b"]["id"]
    assert len(cuerpo["mensajes"]) == 1
    assert cuerpo["mensajes"][0]["plaintext"] == "Mensaje con firma valida"
    assert cuerpo["mensajes"][0]["firmaVerificada"] is True
    assert cuerpo["mensajes"][0]["estadoFirma"] == "VERIFICADO"
    assert cuerpo["mensajes"][0]["alerta"] is None
    assert cuerpo["mensajes"][0]["signature"] is not None


# Verifica deteccion de firma invalida al recuperar mensaje
def testRecuperarMensajeDebeDetectarFirmaInvalida(cliente, usuariosPrueba):
    accessTokenA = obtenerAccessToken(cliente, "a@correo.com", "ClaveSegura123")
    accessTokenB = obtenerAccessToken(cliente, "b@correo.com", "ClaveSegura123")

    respuestaEnvio = cliente.post(
        f"/messages/{usuariosPrueba['b']['id']}",
        json={
            "senderId": usuariosPrueba["a"]["id"],
            "senderPassword": "ClaveSegura123",
            "plaintext": "Mensaje con firma a corromper",
        },
        headers={"Authorization": f"Bearer {accessTokenA}"},
    )

    assert respuestaEnvio.status_code == 201

    messageId = respuestaEnvio.json()["messageId"]

    sesion = SesionLocal()
    try:
        mensaje = sesion.query(Mensaje).filter(Mensaje.id == messageId).first()
        assert mensaje is not None

        mensaje.signature = "firma_invalida_manual"
        sesion.commit()
    finally:
        sesion.close()

    respuestaRecuperacion = cliente.get(
        f"/messages/{usuariosPrueba['b']['id']}?password=ClaveSegura123",
        headers={"Authorization": f"Bearer {accessTokenB}"},
    )

    assert respuestaRecuperacion.status_code == 200

    cuerpo = respuestaRecuperacion.json()

    assert len(cuerpo["mensajes"]) == 1
    assert cuerpo["mensajes"][0]["firmaVerificada"] is False
    assert cuerpo["mensajes"][0]["estadoFirma"] == "NO_VERIFICADO"
    assert (
        cuerpo["mensajes"][0]["alerta"]
        == "Alerta: la firma digital del mensaje no es valida"
    )


# Verifica envio grupal firmado y registro automatico en blockchain
def testEnviarMensajeGrupalFirmadoGeneraFirmaClavesYBloque(cliente, usuariosPrueba):
    groupId = crearGrupoPrueba(cliente, usuariosPrueba)
    accessTokenA = obtenerAccessToken(cliente, "a@correo.com", "ClaveSegura123")

    respuesta = cliente.post(
        f"/groups/{groupId}/messages",
        json={
            "senderId": usuariosPrueba["a"]["id"],
            "senderPassword": "ClaveSegura123",
            "plaintext": "Mensaje grupal firmado para blockchain",
        },
        headers={"Authorization": f"Bearer {accessTokenA}"},
    )

    assert respuesta.status_code == 201

    cuerpo = respuesta.json()

    assert cuerpo["senderId"] == usuariosPrueba["a"]["id"]
    assert cuerpo["groupId"] == groupId
    assert cuerpo["signature"] is not None
    assert cuerpo["signature"] != ""
    assert cuerpo["encryptedKeysGeneradas"] == 3

    sesion = SesionLocal()
    try:
        mensaje = (
            sesion.query(Mensaje).filter(Mensaje.id == cuerpo["messageId"]).first()
        )
        claves = (
            sesion.query(MensajeDestinatario)
            .filter(MensajeDestinatario.messageId == cuerpo["messageId"])
            .all()
        )
        bloques = (
            sesion.query(BloqueBlockchain).order_by(BloqueBlockchain.indice.asc()).all()
        )

        assert mensaje is not None
        assert mensaje.groupId is not None
        assert mensaje.recipientId is None
        assert mensaje.signature is not None
        assert len(claves) == 3
        assert len(bloques) == 2
        assert bloques[1].senderId == usuariosPrueba["a"]["id"]
        assert bloques[1].recipientId == groupId
    finally:
        sesion.close()


# Verifica recuperacion grupal con firma valida
def testRecuperarMensajeGrupalDebeVerificarFirmaValida(cliente, usuariosPrueba):
    groupId = crearGrupoPrueba(cliente, usuariosPrueba)
    accessTokenA = obtenerAccessToken(cliente, "a@correo.com", "ClaveSegura123")
    accessTokenC = obtenerAccessToken(cliente, "c@correo.com", "ClaveSegura123")

    respuestaEnvio = cliente.post(
        f"/groups/{groupId}/messages",
        json={
            "senderId": usuariosPrueba["a"]["id"],
            "senderPassword": "ClaveSegura123",
            "plaintext": "Mensaje grupal con firma valida",
        },
        headers={"Authorization": f"Bearer {accessTokenA}"},
    )

    assert respuestaEnvio.status_code == 201

    respuestaRecuperacion = cliente.get(
        f"/messages/{usuariosPrueba['c']['id']}?password=ClaveSegura123",
        headers={"Authorization": f"Bearer {accessTokenC}"},
    )

    assert respuestaRecuperacion.status_code == 200

    cuerpo = respuestaRecuperacion.json()

    assert len(cuerpo["mensajes"]) == 1
    assert cuerpo["mensajes"][0]["groupId"] == groupId
    assert cuerpo["mensajes"][0]["plaintext"] == "Mensaje grupal con firma valida"
    assert cuerpo["mensajes"][0]["firmaVerificada"] is True
    assert cuerpo["mensajes"][0]["estadoFirma"] == "VERIFICADO"
    assert cuerpo["mensajes"][0]["alerta"] is None


# Verifica que el endpoint de blockchain retorne la cadena completa
def testBlockchainEndpointDebeRetornarCadenaCompleta(cliente, usuariosPrueba):
    accessTokenA = obtenerAccessToken(cliente, "a@correo.com", "ClaveSegura123")

    cliente.post(
        f"/messages/{usuariosPrueba['b']['id']}",
        json={
            "senderId": usuariosPrueba["a"]["id"],
            "senderPassword": "ClaveSegura123",
            "plaintext": "Mensaje para revisar blockchain",
        },
        headers={"Authorization": f"Bearer {accessTokenA}"},
    )

    respuesta = cliente.get("/blockchain")

    assert respuesta.status_code == 200

    cuerpo = respuesta.json()

    assert len(cuerpo) == 2
    assert cuerpo[0]["indice"] == 0
    assert cuerpo[1]["indice"] == 1
    assert cuerpo[1]["senderId"] == usuariosPrueba["a"]["id"]
    assert cuerpo[1]["recipientId"] == usuariosPrueba["b"]["id"]


# Verifica que el endpoint de verificacion detecte cadena valida
def testBlockchainVerifyDebeRetornarCadenaValida(cliente, usuariosPrueba):
    accessTokenA = obtenerAccessToken(cliente, "a@correo.com", "ClaveSegura123")

    cliente.post(
        f"/messages/{usuariosPrueba['b']['id']}",
        json={
            "senderId": usuariosPrueba["a"]["id"],
            "senderPassword": "ClaveSegura123",
            "plaintext": "Mensaje para validar cadena",
        },
        headers={"Authorization": f"Bearer {accessTokenA}"},
    )

    respuesta = cliente.get("/blockchain/verify")

    assert respuesta.status_code == 200

    cuerpo = respuesta.json()

    assert cuerpo["esValida"] is True
    assert cuerpo["cantidadBloques"] == 2
    assert cuerpo["detalle"] == "Cadena valida"


# Verifica que el endpoint de verificacion detecte corrupcion de hash
def testBlockchainVerifyDebeDetectarCorrupcion(cliente, usuariosPrueba):
    accessTokenA = obtenerAccessToken(cliente, "a@correo.com", "ClaveSegura123")

    cliente.post(
        f"/messages/{usuariosPrueba['b']['id']}",
        json={
            "senderId": usuariosPrueba["a"]["id"],
            "senderPassword": "ClaveSegura123",
            "plaintext": "Mensaje para corromper blockchain",
        },
        headers={"Authorization": f"Bearer {accessTokenA}"},
    )

    sesion = SesionLocal()
    try:
        bloque = (
            sesion.query(BloqueBlockchain).filter(BloqueBlockchain.indice == 1).first()
        )
        assert bloque is not None

        bloque.messageHash = "a" * 64
        sesion.commit()
    finally:
        sesion.close()

    respuesta = cliente.get("/blockchain/verify")

    assert respuesta.status_code == 200

    cuerpo = respuesta.json()

    assert cuerpo["esValida"] is False
    assert cuerpo["cantidadBloques"] == 2
    assert "Hash invalido en bloque 1" in cuerpo["detalle"]
