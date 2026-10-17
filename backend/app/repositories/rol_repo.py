from app.repositories.base import BaseRepository


class RolRepository(BaseRepository):
    tabla = "roles"
    columnas = ["nombre", "descripcion"]

    def obtener_por_nombre(self, nombre: str) -> dict | None:
        return self._uno("SELECT * FROM roles WHERE nombre = %s", (nombre,))
