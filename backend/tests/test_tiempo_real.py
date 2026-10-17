import pytest
from starlette.websockets import WebSocketDisconnect


def _token(client, correo):
    from scripts.seed import PASSWORD_DEMO
    return client.post("/auth/token", data={"username": correo, "password": PASSWORD_DEMO}).json()["access_token"]


def test_websocket_rechaza_token_invalido(client):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws?token=falso") as ws:
            ws.receive_json()


def test_notificacion_llega_en_tiempo_real(client, login, datos):
    token = _token(client, "ana.sanchez@correo.com")
    with client.websocket_connect(f"/ws?token={token}") as ws:
        assert ws.receive_json()["evento"] == "conectado"
        client.post("/comunicados/", headers=login("doc2"), json={
            "titulo": "Feria de ciencias", "contenido": "Inscripciones abiertas", "grupo_id": datos["grupos"]["6B"]["id"]})
        evento = ws.receive_json()
        assert evento["evento"] == "notificacion"
        assert evento["datos"]["titulo"] == "Feria de ciencias"


def test_mensaje_de_grupo_llega_en_tiempo_real(client, login, datos):
    token = _token(client, "jorge.perez@correo.com")
    with client.websocket_connect(f"/ws?token={token}") as ws:
        ws.receive_json()
        client.post("/mensajes/", headers=login("doc1"),
                    json={"grupo_id": datos["grupos"]["5A"]["id"], "contenido": "Recuerden la autorización"})
        evento = ws.receive_json()
        assert evento["evento"] == "mensaje" and evento["datos"]["contenido"] == "Recuerden la autorización"
        ws.send_text("ping")
        assert ws.receive_json()["evento"] == "pong"
