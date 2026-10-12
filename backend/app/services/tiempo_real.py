"""
Tiempo real con WebSockets.

Cada usuario logueado abre una conexión WebSocket (/ws?token=...). Cuando
ocurre algo que le interesa (nueva notificación, mensaje en su curso, etc.)
el servidor le "empuja" un evento JSON sin que el frontend tenga que preguntar:

    {"evento": "notificacion", "datos": {...}}
    {"evento": "mensaje",      "datos": {...}}

Los endpoints normales son síncronos (corren en hilos), así que se usa
asyncio.run_coroutine_threadsafe para enviar desde esos hilos al event loop.
"""
import asyncio
from collections import defaultdict

from fastapi import WebSocket
from fastapi.encoders import jsonable_encoder


class GestorConexiones:
    def __init__(self):
        self._conexiones: dict[int, set[WebSocket]] = defaultdict(set)
        self._loop: asyncio.AbstractEventLoop | None = None

    async def conectar(self, usuario_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self._loop = asyncio.get_running_loop()
        self._conexiones[usuario_id].add(ws)   # un usuario puede tener varias pestañas abiertas

    def desconectar(self, usuario_id: int, ws: WebSocket) -> None:
        self._conexiones[usuario_id].discard(ws)
        if not self._conexiones[usuario_id]:
            self._conexiones.pop(usuario_id, None)

    def conectados(self) -> list[int]:
        return list(self._conexiones.keys())

    async def _enviar_a(self, usuario_id: int, payload: dict) -> None:
        for ws in list(self._conexiones.get(usuario_id, ())):
            try:
                await ws.send_json(payload)
            except Exception:
                self.desconectar(usuario_id, ws)

    def enviar(self, usuario_ids: list[int], evento: str, datos) -> None:
        """Envía un evento a varios usuarios. Seguro de llamar desde cualquier hilo."""
        if self._loop is None or self._loop.is_closed():
            return
        payload = {"evento": evento, "datos": jsonable_encoder(datos)}
        for uid in set(usuario_ids):
            if uid in self._conexiones:
                asyncio.run_coroutine_threadsafe(self._enviar_a(uid, payload), self._loop)


gestor = GestorConexiones()
