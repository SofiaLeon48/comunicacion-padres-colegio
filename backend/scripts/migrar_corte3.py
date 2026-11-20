"""
Migración del corte 3 para una base que YA tiene datos (Neon en producción).

Agrega el módulo "Tablero", actualiza la descripción del módulo "Reportes" y
asigna los permisos, SIN borrar nada. Se puede ejecutar varias veces.

    python -m scripts.migrar_corte3
"""
import psycopg2

from app.core.config import settings

SQL = """
INSERT INTO modulos (clave, nombre, descripcion, ruta, icono, orden)
VALUES ('tablero', 'Tablero', 'Dashboard de indicadores publicado (iframe)', '/tablero', 'bi-speedometer2', 8)
ON CONFLICT (clave) DO NOTHING;

UPDATE modulos SET descripcion = 'Reportes en PDF y Excel con envío por correo',
                   icono = 'bi-file-earmark-bar-graph', orden = 9
WHERE clave = 'reportes';
UPDATE modulos SET orden = 10 WHERE clave = 'configuracion';

INSERT INTO rol_modulo (rol_id, modulo_id)
SELECT r.id, m.id FROM roles r JOIN modulos m ON m.clave = 'tablero'
WHERE r.nombre IN ('coordinacion', 'docente')
  AND NOT EXISTS (SELECT 1 FROM rol_modulo rm WHERE rm.rol_id = r.id AND rm.modulo_id = m.id);
"""

if __name__ == "__main__":
    if not settings.DATABASE_URL:
        raise SystemExit("Falta DATABASE_URL en el archivo .env")
    with psycopg2.connect(settings.DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute(SQL)
        cur.execute("SELECT clave, orden FROM modulos ORDER BY orden")
        print("✔ Migración aplicada. Módulos:", ", ".join(f"{c}({o})" for c, o in cur.fetchall()))
