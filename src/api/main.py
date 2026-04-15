from fastapi import FastAPI
from sqlalchemy import text

from src.auth.baseDatos import Base, motorBaseDatos, SesionLocal
from src.auth.configuracion import configuracion
from src.auth.esquemas import EstadoServicioSalida


Base.metadata.create_all(bind=motorBaseDatos)
app = FastAPI(title=configuracion.APPNombre, version=configuracion.APIVersion)


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
