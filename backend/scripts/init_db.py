"""
Crea (o recrea) las 12 tablas ejecutando database/schema.sql contra DATABASE_URL.

    python -m scripts.init_db

¡CUIDADO! Borra las tablas existentes y todos sus datos.
"""
import pathlib
import sys

import psycopg2

from app.core.config import settings

ESQUEMA = pathlib.Path(__file__).resolve().parent.parent / "database" / "schema.sql"


def crear_esquema(dsn: str) -> None:
    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(ESQUEMA.read_text(encoding="utf-8"))


if __name__ == "__main__":
    if not settings.DATABASE_URL:
        sys.exit("Falta DATABASE_URL en el archivo .env")
    if "--si" not in sys.argv:
        r = input("Esto BORRA y recrea todas las tablas. ¿Continuar? (s/N): ")
        if r.strip().lower() != "s":
            sys.exit("Cancelado.")
    crear_esquema(settings.DATABASE_URL)
    print("✔ Esquema creado: 12 tablas + 4 roles base.")
