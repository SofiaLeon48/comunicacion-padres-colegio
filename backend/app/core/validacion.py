"""
Ayudas para usar la clase de cada tabla (app/models) al crear y al editar.

Como cada tabla tiene UNA sola clase con todos sus atributos opcionales, las rutas deciden:
  - qué campos son obligatorios al crear  → obligatorios(datos, "nombre", "grado")
  - qué campos se aceptan del cliente      → campos(datos, "nombre", "grado", ...)
Todo lo que no se nombre (id, creado, modificado, estado, autor, fechas automáticas...) se ignora.
"""
from fastapi import HTTPException
from pydantic import BaseModel


def obligatorios(datos: BaseModel, *nombres: str) -> None:
    """Responde 422 si falta alguno de los campos obligatorios para crear."""
    faltan = [n for n in nombres
              if getattr(datos, n) is None or (isinstance(getattr(datos, n), str) and not getattr(datos, n).strip())]
    if faltan:
        raise HTTPException(status_code=422, detail=f"Faltan campos obligatorios: {', '.join(faltan)}.")


def campos(datos: BaseModel, *nombres: str, editar: bool = False) -> dict:
    """Devuelve solo los campos permitidos.
    Al crear: los que vienen con valor (los vacíos los completa la base de datos con su valor por defecto).
    Al editar: solo los que el cliente envió (así se puede, por ejemplo, quitar un director con null)."""
    if editar:
        return datos.model_dump(include=set(nombres), exclude_unset=True)
    return datos.model_dump(include=set(nombres), exclude_none=True)
