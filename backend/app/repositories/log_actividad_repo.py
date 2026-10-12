from datetime import datetime

from app.repositories.base import BaseRepository


class LogActividadRepository(BaseRepository):
    tabla = "logs_actividad"
    columnas = ["usuario_id", "accion", "entidad", "entidad_id", "detalle"]
    orden = "fecha"

    def registrar(self, usuario_id: int | None, accion: str, entidad: str,
                  entidad_id: int | None = None, detalle: str | None = None) -> None:
        self.crear({"usuario_id": usuario_id, "accion": accion, "entidad": entidad,
                    "entidad_id": entidad_id, "detalle": (detalle or "")[:255] or None})

    def listar_detallado(self, usuario_id: int | None = None, entidad: str | None = None,
                         accion: str | None = None, desde: datetime | None = None,
                         hasta: datetime | None = None, limite: int = 100) -> list[dict]:
        condiciones, valores = ["l.estado = 'activo'"], []
        for campo, valor in (("l.usuario_id", usuario_id), ("l.entidad", entidad), ("l.accion", accion)):
            if valor is not None:
                condiciones.append(f"{campo} = %s")
                valores.append(valor)
        if desde:
            condiciones.append("l.fecha >= %s")
            valores.append(desde)
        if hasta:
            condiciones.append("l.fecha < %s")
            valores.append(hasta)
        valores.append(limite)
        return self._todos(f"""
            SELECT l.*, u.nombre AS usuario_nombre
            FROM logs_actividad l
            LEFT JOIN usuarios u ON u.id = l.usuario_id
            WHERE {" AND ".join(condiciones)}
            ORDER BY l.fecha DESC, l.id DESC
            LIMIT %s
        """, valores)
