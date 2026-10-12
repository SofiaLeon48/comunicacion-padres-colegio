from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from fastapi.concurrency import run_in_threadpool

from app.core.deps import obtener_usuario_desde_token
from app.services.tiempo_real import gestor

router = APIRouter(tags=["Tiempo real"])


@router.websocket("/ws")
async def websocket(ws: WebSocket, token: str = Query(...)):
    """Conexión en tiempo real. El frontend se conecta a  ws://HOST/ws?token=<JWT>
    y recibe eventos JSON: notificacion, mensaje, mensajes_leidos."""
    usuario = await run_in_threadpool(obtener_usuario_desde_token, token)
    if not usuario:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await gestor.conectar(usuario["id"], ws)
    try:
        await ws.send_json({"evento": "conectado", "datos": {"usuario_id": usuario["id"]}})
        while True:
            # El cliente puede enviar "ping" para mantener viva la conexión
            if await ws.receive_text() == "ping":
                await ws.send_json({"evento": "pong", "datos": None})
    except WebSocketDisconnect:
        pass
    finally:
        gestor.desconectar(usuario["id"], ws)
