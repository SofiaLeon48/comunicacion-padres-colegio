"""
Capa 1 — Conexión a PostgreSQL (Neon).

Usa un *pool* de conexiones: en vez de abrir una conexión nueva por cada
consulta (lento con una BD en la nube), se reutilizan conexiones abiertas.

Uso en los repositories:

    with get_cursor() as cur:
        cur.execute("SELECT ...", (param,))
        filas = cur.fetchall()

Al salir del bloque `with` se hace COMMIT automáticamente; si ocurre un error
se hace ROLLBACK y el error se relanza para que la capa API lo traduzca.
"""
from contextlib import contextmanager
from threading import Lock

from psycopg2 import OperationalError
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

from app.core.config import settings


class BaseDeDatosNoDisponible(Exception):
    """No se pudo conectar con la base de datos."""


_pool: ThreadedConnectionPool | None = None
_lock = Lock()


def _obtener_pool() -> ThreadedConnectionPool:
    global _pool
    if _pool is None:
        with _lock:
            if _pool is None:
                if not settings.DATABASE_URL:
                    raise BaseDeDatosNoDisponible("DATABASE_URL no está configurada en el archivo .env")
                try:
                    _pool = ThreadedConnectionPool(
                        minconn=1,
                        maxconn=10,
                        dsn=settings.DATABASE_URL,
                        cursor_factory=RealDictCursor,
                        # keepalives: evitan que Neon corte conexiones inactivas sin avisar
                        keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3,
                    )
                except OperationalError as e:
                    raise BaseDeDatosNoDisponible(str(e)) from e
    return _pool


def _conexion_viva(conn) -> bool:
    if conn.closed:
        return False
    try:
        with conn.cursor() as c:
            c.execute("SELECT 1")
        conn.rollback()
        return True
    except OperationalError:
        return False


@contextmanager
def get_cursor():
    pool = _obtener_pool()
    conn = pool.getconn()
    # Neon suspende la BD tras inactividad: si la conexión murió, se descarta y se pide otra
    if not _conexion_viva(conn):
        pool.putconn(conn, close=True)
        try:
            conn = pool.getconn()
        except OperationalError as e:
            raise BaseDeDatosNoDisponible(str(e)) from e
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def cerrar_pool():
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
