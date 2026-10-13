from app.repositories.base import BaseRepository


class ModuloRepository(BaseRepository):
    tabla = "modulos"
    columnas = ["clave", "nombre", "descripcion", "ruta", "icono", "orden"]
    orden = "orden"
