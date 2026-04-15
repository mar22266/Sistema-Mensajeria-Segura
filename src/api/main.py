from fastapi import FastAPI
from sqlalchemy import text

from src.auth import modelos
from src.auth.baseDatos import Base, SesionLocal, motorBaseDatos
from src.auth.configuracion import configuracion
from src.auth.esquemas import EstadoServicioSalida
from src.auth.rutas import routerAuth
from src.users.rutas import routerUsers

Base.metadata.create_all(bind=motorBaseDatos)

app = FastAPI(title=configuracion.APPNombre, version=configuracion.APIVersion)

app.include_router(routerAuth)
app.include_router(routerUsers)


# Verifica que la API este activa
@app.get("/", response_model=EstadoServicioSalida)
def inicio():
    return EstadoServicioSalida(
        estado="ok", servicio=configuracion.APPNombre, version=configuracion.APIVersion
    )


# Verifica conexion con PostgreSQL
@app.get("/salud/db")
def saludBaseDatos():
    sesion = SesionLocal()
    try:
        sesion.execute(text("SELECT 1"))
        return {"estado": "ok", "baseDatos": "conectada"}
    finally:
        sesion.close()
