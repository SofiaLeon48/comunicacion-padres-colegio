"""
Configuración de pruebas.

Las pruebas corren contra una base PostgreSQL REAL (no simulada). Usa una base
separada de la de producción, definida en TEST_DATABASE_URL, por ejemplo:

    TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/colegio_test

(puede ser también una rama "test" de Neon). Antes de CADA prueba se recrean
las tablas y se cargan los datos de demostración, así las pruebas no dependen
unas de otras.
"""
import os

import pytest

TEST_DB = os.getenv("TEST_DATABASE_URL")
if not TEST_DB:
    pytest.exit("Define TEST_DATABASE_URL para correr las pruebas (ver tests/conftest.py).", returncode=1)
os.environ["DATABASE_URL"] = TEST_DB
os.environ.setdefault("JWT_SECRET", "clave-de-pruebas-0123456789abcdef0123456789abcdef")
os.environ["SMTP_HOST"] = ""

from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import settings  # noqa: E402

settings.DATABASE_URL = TEST_DB
settings.JWT_SECRET = os.environ["JWT_SECRET"]
settings.SMTP_HOST = ""

from main import app  # noqa: E402
from scripts.init_db import crear_esquema  # noqa: E402
from scripts.seed import PASSWORD_DEMO, sembrar  # noqa: E402

CORREOS = {
    "coord": "coordinacion@colegio.edu.co",
    "doc1": "lmartinez@colegio.edu.co",     # director 5A
    "doc2": "cgomez@colegio.edu.co",        # director 6B
    "maria": "maria.rodriguez@correo.com",  # hijos en 5A y 6B
    "jorge": "jorge.perez@correo.com",      # hijo en 5A (Samuel)
    "ana": "ana.sanchez@correo.com",        # hija en 6B
    "laura": "laura.diaz@correo.com",       # también acudiente de Samuel (5A)
    "carlos": "carlos.mendoza@correo.com",  # hijos en 3A y 9A
}

ROL = {"coord": "coordinacion", "doc1": "docente", "doc2": "docente"}


@pytest.fixture()
def datos():
    crear_esquema(TEST_DB)
    return sembrar()


@pytest.fixture()
def client(datos):
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def login(client):
    """login("maria") -> headers con el token de ese usuario."""
    cache = {}

    def _login(quien: str) -> dict:
        if quien not in cache:
            r = client.post("/auth/login", json={"correo": CORREOS[quien], "password": PASSWORD_DEMO,
                                                 "rol": ROL.get(quien, "acudiente")})
            assert r.status_code == 200, r.text
            cache[quien] = {"Authorization": f"Bearer {r.json()['access_token']}"}
        return cache[quien]
    return _login
