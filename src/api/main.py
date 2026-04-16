from fastapi import FastAPI
from sqlalchemy import text

from src.auth import modelos
from src.blockchain import modelos as modelosBlockchain
from src.blockchain.servicio import asegurarBloqueGenesis
from src.crypto import modelos as modelosCrypto
from src.auth.baseDatos import Base, SesionLocal, motorBaseDatos
from src.auth.configuracion import configuracion
from src.auth.esquemas import EstadoServicioSalida
from src.auth.rutas import routerAuth
from src.crypto.rutas import routerMessages
from src.users.rutas import routerUsers


Base.metadata.create_all(bind=motorBaseDatos)

app = FastAPI(title=configuracion.APPNombre, version=configuracion.APIVersion)

app.include_router(routerAuth)
app.include_router(routerUsers)
app.include_router(routerMessages)


# Inicializa recursos base del sistema
@app.on_event("startup")
def inicializarSistema():
    sesion = SesionLocal()
    try:
        asegurarBloqueGenesis(sesion)
    finally:
        sesion.close()


# Verifica que la API este activa
@app.get("/", response_model=EstadoServicioSalida)
def inicio():
    return EstadoServicioSalida(
        estado="ok", servicio=configuracion.APPNombre, version=configuracion.APIVersion
    )


# Verifica conexion con base de datos
@app.get("/salud/db")
def saludBaseDatos():
    sesion = SesionLocal()
    try:
        sesion.execute(text("SELECT 1"))
        return {"estado": "ok", "baseDatos": "conectada"}
    finally:
        sesion.close()
