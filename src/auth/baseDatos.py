from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.auth.configuracion import configuracion

# configura conexion a db
motorBaseDatos = create_engine(configuracion.urlBaseDatos, future=True, echo=False)

SesionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=motorBaseDatos, future=True
)

Base = declarative_base()


# Devuelve una sesion de base de datos
def obtenerBaseDatos():
    sesion = SesionLocal()
    try:
        yield sesion
    finally:
        sesion.close()
