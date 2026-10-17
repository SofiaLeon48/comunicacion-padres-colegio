"""
Capa 3 — Repository base (patrón Repository + herencia).

Las 12 tablas comparten las mismas operaciones CRUD. En vez de copiar el mismo
SQL 12 veces, esta clase lo implementa UNA vez y cada repository hijo solo
declara su tabla y sus columnas editables:

    class GrupoRepository(BaseRepository):
        tabla = "grupos"
        columnas = ["nombre", "grado", "jornada", "anio_lectivo", "director_id"]

Los repositories hijos agregan sus consultas especiales (JOINs, reportes...).

Seguridad: los nombres de tabla/columna se insertan con psycopg2.sql.Identifier
y los valores siempre con marcadores %s, así que no hay riesgo de inyección SQL.
"""
from typing import Any

from psycopg2 import sql

from app.core.database import get_cursor


class BaseRepository:
    tabla: str = ""
    columnas: list[str] = []          # columnas que el cliente puede escribir
    orden: str = "id"                 # columna de ordenamiento por defecto

    # ------------------------------------------------------------ utilidades
    @staticmethod
    def _todos(consulta, valores=()) -> list[dict]:
        with get_cursor() as cur:
            cur.execute(consulta, valores)
            return cur.fetchall()

    @staticmethod
    def _uno(consulta, valores=()) -> dict | None:
        with get_cursor() as cur:
            cur.execute(consulta, valores)
            return cur.fetchone()

    # ------------------------------------------------------------ lectura
    def listar(self, incluir_inactivos: bool = False, filtros: dict[str, Any] | None = None,
               limite: int = 200, desplazamiento: int = 0) -> list[dict]:
        condiciones, valores = [], []
        if not incluir_inactivos:
            condiciones.append(sql.SQL("estado = 'activo'"))
        for campo, valor in (filtros or {}).items():
            if valor is not None:
                condiciones.append(sql.SQL("{} = %s").format(sql.Identifier(campo)))
                valores.append(valor)

        consulta = sql.SQL("SELECT * FROM {}").format(sql.Identifier(self.tabla))
        if condiciones:
            consulta += sql.SQL(" WHERE ") + sql.SQL(" AND ").join(condiciones)
        consulta += sql.SQL(" ORDER BY {} LIMIT %s OFFSET %s").format(sql.Identifier(self.orden))
        valores += [limite, desplazamiento]

        with get_cursor() as cur:
            cur.execute(consulta, valores)
            return cur.fetchall()

    def obtener(self, id_: int, incluir_inactivos: bool = False) -> dict | None:
        consulta = sql.SQL("SELECT * FROM {} WHERE id = %s").format(sql.Identifier(self.tabla))
        if not incluir_inactivos:
            consulta += sql.SQL(" AND estado = 'activo'")
        with get_cursor() as cur:
            cur.execute(consulta, (id_,))
            return cur.fetchone()

    # ------------------------------------------------------------ escritura
    def crear(self, datos: dict[str, Any]) -> dict:
        campos = [c for c in self.columnas if c in datos]
        consulta = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *").format(
            sql.Identifier(self.tabla),
            sql.SQL(", ").join(map(sql.Identifier, campos)),
            sql.SQL(", ").join(sql.Placeholder() * len(campos)),
        )
        with get_cursor() as cur:
            cur.execute(consulta, [datos[c] for c in campos])
            return cur.fetchone()

    def actualizar(self, id_: int, datos: dict[str, Any]) -> dict | None:
        """Actualización parcial: solo cambia los campos recibidos.
        'modificado' lo actualiza el TRIGGER de la base de datos."""
        campos = [c for c in self.columnas + ["estado"] if c in datos]
        if not campos:
            return self.obtener(id_, incluir_inactivos=True)
        consulta = sql.SQL("UPDATE {} SET {} WHERE id = %s RETURNING *").format(
            sql.Identifier(self.tabla),
            sql.SQL(", ").join(sql.SQL("{} = %s").format(sql.Identifier(c)) for c in campos),
        )
        with get_cursor() as cur:
            cur.execute(consulta, [datos[c] for c in campos] + [id_])
            return cur.fetchone()

    def desactivar(self, id_: int) -> bool:
        """Borrado LÓGICO: marca el registro como 'inactivo' (conserva el historial)."""
        consulta = sql.SQL(
            "UPDATE {} SET estado = 'inactivo' WHERE id = %s AND estado = 'activo' RETURNING id"
        ).format(sql.Identifier(self.tabla))
        with get_cursor() as cur:
            cur.execute(consulta, (id_,))
            return cur.fetchone() is not None

    def reactivar(self, id_: int) -> bool:
        consulta = sql.SQL(
            "UPDATE {} SET estado = 'activo' WHERE id = %s AND estado = 'inactivo' RETURNING id"
        ).format(sql.Identifier(self.tabla))
        with get_cursor() as cur:
            cur.execute(consulta, (id_,))
            return cur.fetchone() is not None
