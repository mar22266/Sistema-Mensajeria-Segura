from src.auth.baseDatos import SesionLocal
from src.auth.modelos import Usuario


# Verifica activacion de mfa y generacion de qr
def testHabilitarMfaDebeRetornarQrYOtpauth(cliente, usuarioRegistrado):
    loginRespuesta = cliente.post(
        "/auth/login",
        json={
            "email": "andre@correo.com",
            "password": "ClaveSegura123",
        },
    )

    assert loginRespuesta.status_code == 200
    accessToken = loginRespuesta.json()["accessToken"]

    respuesta = cliente.post(
        "/auth/mfa/enable",
        json={
            "userId": usuarioRegistrado["datos"]["id"],
        },
        headers={"Authorization": f"Bearer {accessToken}"},
    )

    assert respuesta.status_code == 200

    cuerpo = respuesta.json()

    assert cuerpo["userId"] == usuarioRegistrado["datos"]["id"]
    assert cuerpo["email"] == "andre@correo.com"
    assert cuerpo["mfaActiva"] is True
    assert cuerpo["otpauthUrl"].startswith("otpauth://totp/")
    assert cuerpo["qrBase64"].startswith("data:image/png;base64,")

    sesion = SesionLocal()
    try:
        usuario = (
            sesion.query(Usuario).filter(Usuario.email == "andre@correo.com").first()
        )
        assert usuario is not None
        assert usuario.totpSecret is not None
        assert usuario.totpSecret != ""
    finally:
        sesion.close()


# Verifica que no se pueda activar mfa para otro usuario
def testHabilitarMfaDebeRechazarOtroUsuario(cliente, usuariosPrueba):
    loginRespuesta = cliente.post(
        "/auth/login",
        json={
            "email": "a@correo.com",
            "password": "ClaveSegura123",
        },
    )

    assert loginRespuesta.status_code == 200
    accessToken = loginRespuesta.json()["accessToken"]

    respuesta = cliente.post(
        "/auth/mfa/enable",
        json={
            "userId": usuariosPrueba["b"]["id"],
        },
        headers={"Authorization": f"Bearer {accessToken}"},
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == "No puede activar MFA para otro usuario"


# Verifica login normal cuando mfa no esta activa
def testLoginSinMfaDebeRetornarTokens(cliente, usuarioRegistrado):
    respuesta = cliente.post(
        "/auth/login",
        json={
            "email": "andre@correo.com",
            "password": "ClaveSegura123",
        },
    )

    assert respuesta.status_code == 200

    cuerpo = respuesta.json()

    assert cuerpo["requiereMfa"] is False
    assert cuerpo["mfaActiva"] is False
    assert cuerpo["accessToken"] is not None
    assert cuerpo["refreshToken"] is not None
    assert cuerpo["tokenType"] == "bearer"


# Verifica login inicial cuando mfa esta activa y exige segundo paso
def testLoginConMfaActivaDebeExigirSegundoPaso(cliente, usuarioRegistrado):
    loginInicial = cliente.post(
        "/auth/login",
        json={
            "email": "andre@correo.com",
            "password": "ClaveSegura123",
        },
    )

    assert loginInicial.status_code == 200
    accessToken = loginInicial.json()["accessToken"]

    habilitarRespuesta = cliente.post(
        "/auth/mfa/enable",
        json={
            "userId": usuarioRegistrado["datos"]["id"],
        },
        headers={"Authorization": f"Bearer {accessToken}"},
    )

    assert habilitarRespuesta.status_code == 200

    respuesta = cliente.post(
        "/auth/login",
        json={
            "email": "andre@correo.com",
            "password": "ClaveSegura123",
        },
    )

    assert respuesta.status_code == 200

    cuerpo = respuesta.json()

    assert cuerpo["requiereMfa"] is True
    assert cuerpo["mfaActiva"] is True
    assert cuerpo["accessToken"] is None
    assert cuerpo["refreshToken"] is None


# Verifica endpoint de verificacion totp con codigo valido
def testVerificarMfaConCodigoValido(cliente, usuarioRegistrado):
    from tests.conftest import generarCodigoTotp

    loginInicial = cliente.post(
        "/auth/login",
        json={
            "email": "andre@correo.com",
            "password": "ClaveSegura123",
        },
    )

    accessToken = loginInicial.json()["accessToken"]

    cliente.post(
        "/auth/mfa/enable",
        json={
            "userId": usuarioRegistrado["datos"]["id"],
        },
        headers={"Authorization": f"Bearer {accessToken}"},
    )

    codigoTotp = generarCodigoTotp("andre@correo.com")

    respuesta = cliente.post(
        "/auth/mfa/verify",
        json={
            "email": "andre@correo.com",
            "codigoTotp": codigoTotp,
        },
    )

    assert respuesta.status_code == 200

    cuerpo = respuesta.json()

    assert cuerpo["email"] == "andre@correo.com"
    assert cuerpo["codigoValido"] is True
    assert cuerpo["mensaje"] == "Codigo TOTP valido"


# Verifica login final con mfa y emision de tokens
def testLoginConMfaDebeRetornarTokens(cliente, usuarioRegistrado):
    from tests.conftest import generarCodigoTotp

    loginInicial = cliente.post(
        "/auth/login",
        json={
            "email": "andre@correo.com",
            "password": "ClaveSegura123",
        },
    )

    accessToken = loginInicial.json()["accessToken"]

    cliente.post(
        "/auth/mfa/enable",
        json={
            "userId": usuarioRegistrado["datos"]["id"],
        },
        headers={"Authorization": f"Bearer {accessToken}"},
    )

    codigoTotp = generarCodigoTotp("andre@correo.com")

    respuesta = cliente.post(
        "/auth/mfa/login",
        json={
            "email": "andre@correo.com",
            "password": "ClaveSegura123",
            "codigoTotp": codigoTotp,
        },
    )

    assert respuesta.status_code == 200

    cuerpo = respuesta.json()

    assert cuerpo["accessToken"] is not None
    assert cuerpo["refreshToken"] is not None
    assert cuerpo["tokenType"] == "bearer"
    assert cuerpo["email"] == "andre@correo.com"
    assert cuerpo["mensaje"] == "Inicio de sesion con MFA exitoso"


# Verifica login con mfa usando codigo invalido
def testLoginConMfaDebeFallarConCodigoInvalido(cliente, usuarioRegistrado):
    loginInicial = cliente.post(
        "/auth/login",
        json={
            "email": "andre@correo.com",
            "password": "ClaveSegura123",
        },
    )

    accessToken = loginInicial.json()["accessToken"]

    cliente.post(
        "/auth/mfa/enable",
        json={
            "userId": usuarioRegistrado["datos"]["id"],
        },
        headers={"Authorization": f"Bearer {accessToken}"},
    )

    respuesta = cliente.post(
        "/auth/mfa/login",
        json={
            "email": "andre@correo.com",
            "password": "ClaveSegura123",
            "codigoTotp": "000000",
        },
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "Codigo TOTP invalido"


# Verifica refresh token correcto
def testRefreshTokenDebeRetornarNuevaSesion(cliente, usuarioRegistrado):
    loginRespuesta = cliente.post(
        "/auth/login",
        json={
            "email": "andre@correo.com",
            "password": "ClaveSegura123",
        },
    )

    refreshToken = loginRespuesta.json()["refreshToken"]

    respuesta = cliente.post(
        "/auth/refresh",
        json={
            "refreshToken": refreshToken,
        },
    )

    assert respuesta.status_code == 200

    cuerpo = respuesta.json()

    assert cuerpo["accessToken"] is not None
    assert cuerpo["refreshToken"] is not None
    assert cuerpo["tokenType"] == "bearer"


# Verifica refresh token invalido
def testRefreshTokenDebeFallarSiEsInvalido(cliente):
    respuesta = cliente.post(
        "/auth/refresh",
        json={
            "refreshToken": "token_invalido_manual",
        },
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == "Refresh token invalido o expirado"
