"""Corte 3: módulo Tablero (publicado con iframe), módulo Reporte (PDF/Excel/correo) e IA."""
import json

import httpx
import pytest

from app.core.config import settings


# ---------------------------------------------------------------- Tablero
def llave(client, login, quien="coord"):
    r = client.get("/tablero/enlace", headers=login(quien))
    assert r.status_code == 200, r.text
    return r.json()["llave"]


def test_tablero_enlace_solo_personal_con_modulo(client, login):
    assert client.get("/tablero/enlace", headers=login("maria")).status_code == 403
    assert client.get("/tablero/enlace", headers=login("doc1")).status_code == 200
    assert client.get("/tablero/enlace").status_code == 401


def test_tablero_publicado_exige_llave(client, login):
    t = llave(client, login)
    pagina = client.get(f"/tablero/publico?t={t}")
    assert pagina.status_code == 200 and "<canvas" in pagina.text
    assert client.get("/tablero/publico?t=otra").status_code == 403
    assert client.get("/tablero/publico/datos?t=otra").status_code == 403
    assert client.get("/static/chart.umd.js").status_code == 200


def test_tablero_datos_4_indicadores_y_6_graficos(client, login):
    t = llave(client, login)
    d = client.get(f"/tablero/publico/datos?t={t}").json()
    assert set(d["indicadores"]) == {"comunicados", "lectura_promedio", "citaciones", "mensajes"}
    graficos = ["comunicados_por_grupo", "lectura_por_grupo", "comunicados_por_prioridad",
                "citaciones_por_estado", "asistencia_citaciones", "actividad"]
    assert all(g in d for g in graficos)
    assert d["indicadores"]["comunicados"] == sum(x["valor"] for x in d["comunicados_por_grupo"])


def test_tablero_filtros_grupo_y_fechas(client, login, datos):
    t = llave(client, login)
    g5a = datos["grupos"]["5A"]["id"]
    todo = client.get(f"/tablero/publico/datos?t={t}").json()["indicadores"]
    solo5a = client.get(f"/tablero/publico/datos?t={t}&grupo_id={g5a}").json()
    assert solo5a["indicadores"]["comunicados"] < todo["comunicados"]
    assert {x["etiqueta"] for x in solo5a["comunicados_por_grupo"]} == {"5A"}
    vacio = client.get(f"/tablero/publico/datos?t={t}&desde=2000-01-01&hasta=2000-12-31").json()
    assert vacio["indicadores"] == {"comunicados": 0, "lectura_promedio": 0.0, "citaciones": 0, "mensajes": 0}
    assert client.get(f"/tablero/publico/datos?t={t}&desde=2026-12-01&hasta=2026-01-01").status_code == 422
    grupos = client.get(f"/tablero/publico/grupos?t={t}").json()
    assert any(g["nombre"].startswith("5A") for g in grupos)


# ---------------------------------------------------------------- Reportes
def test_reporte_sin_ids_y_con_criterios(client, login):
    h = login("coord")
    for tipo in ("comunicados", "citaciones"):
        r = client.get(f"/reportes/datos?tipo={tipo}", headers=h).json()
        assert r["filas"], tipo
        for fila in r["filas"]:
            assert not any(k == "id" or k.endswith("_id") for k in fila), fila
        assert set(r["criterios"]) >= {"Periodo", "Grupo"}
    citas = client.get("/reportes/datos?tipo=citaciones&estado=realizada", headers=h).json()["filas"]
    assert citas and all(f["estado"] == "Realizada" for f in citas)
    urg = client.get("/reportes/datos?tipo=comunicados&estado=urgente", headers=h).json()["filas"]
    assert urg and all(f["prioridad"] == "Urgente" for f in urg)


def test_reporte_validaciones_y_permisos(client, login):
    h = login("coord")
    assert client.get("/reportes/datos?tipo=otro", headers=h).status_code == 422
    assert client.get("/reportes/datos?tipo=citaciones&estado=rara", headers=h).status_code == 422
    assert client.get("/reportes/datos?tipo=citaciones&desde=2026-12-01&hasta=2026-01-01", headers=h).status_code == 422
    assert client.get("/reportes/datos?tipo=citaciones", headers=login("maria")).status_code == 403
    assert client.get("/reportes/datos?tipo=citaciones", headers=login("doc1")).status_code == 200


def test_exportar_pdf_y_excel(client, login, datos):
    h = login("coord")
    g = datos["grupos"]["5A"]["id"]
    pdf = client.get(f"/reportes/exportar?tipo=comunicados&formato=pdf&grupo_id={g}&desde=2020-01-01", headers=h)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    assert "attachment" in pdf.headers["content-disposition"]
    xlsx = client.get("/reportes/exportar?tipo=citaciones&formato=excel", headers=h)
    assert xlsx.status_code == 200 and xlsx.content[:2] == b"PK"
    from io import BytesIO
    from openpyxl import load_workbook
    hoja = load_workbook(BytesIO(xlsx.content)).active
    assert "Conecta Escolar" in hoja["A1"].value and hoja["A6"].value == "Fecha y hora"


def test_enviar_reporte_sin_correo_configurado(client, login):
    r = client.post("/reportes/enviar", headers=login("coord"),
                    json={"tipo": "citaciones", "formato": "pdf", "correo": "rector@colegio.edu.co"})
    assert r.status_code == 503


def test_enviar_reporte_con_brevo(client, login, monkeypatch):
    enviados = []
    monkeypatch.setattr(settings, "BREVO_API_KEY", "llave-prueba")
    monkeypatch.setattr(settings, "CORREO_REMITENTE", "colegio@ejemplo.com")

    def falso_post(url, json=None, headers=None, timeout=None):
        enviados.append((url, json, headers))
        return httpx.Response(201, json={"messageId": "x"})

    monkeypatch.setattr(httpx, "post", falso_post)
    r = client.post("/reportes/enviar", headers=login("coord"),
                    json={"tipo": "comunicados", "formato": "excel", "correo": "rector@colegio.edu.co",
                          "mensaje": "Para la reunión del consejo"})
    assert r.status_code == 200, r.text
    url, cuerpo, headers = enviados[0]
    assert "brevo" in url and headers["api-key"] == "llave-prueba"
    assert cuerpo["to"] == [{"email": "rector@colegio.edu.co"}]
    assert cuerpo["attachment"][0]["name"].endswith(".xlsx")


# ---------------------------------------------------------------- IA
def test_ia_desactivada_responde_503(client, login):
    assert client.get("/ia/estado", headers=login("coord")).json() == {"habilitada": False}
    r = client.post("/ia/redactar-comunicado", headers=login("doc1"), json={"idea": "Reunión de padres el viernes"})
    assert r.status_code == 503
    assert client.post("/ia/redactar-comunicado", headers=login("maria"),
                       json={"idea": "Reunión de padres el viernes"}).status_code == 403


@pytest.fixture()
def gemini_falso(monkeypatch):
    llamadas = []
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "llave-prueba")

    def respuesta(texto):
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": texto}]}}]},
                              request=httpx.Request("POST", "https://x"))

    def falso_post(url, json=None, headers=None, timeout=None):
        llamadas.append(json)
        if json["generationConfig"].get("responseMimeType") == "application/json":
            return respuesta(__import__("json").dumps({"titulo": "Reunión de padres", "contenido": "Cordial saludo..."}))
        return respuesta("• Hallazgo 1\n• Recomendación 1")

    monkeypatch.setattr(httpx, "post", falso_post)
    return llamadas


def test_ia_redacta_comunicado(client, login, gemini_falso):
    r = client.post("/ia/redactar-comunicado", headers=login("doc1"),
                    json={"idea": "Reunión de padres el viernes a las 7 am", "tono": "cercano"})
    assert r.status_code == 200 and r.json()["titulo"] == "Reunión de padres"
    assert "cercano" in gemini_falso[0]["contents"][0]["parts"][0]["text"]


def test_ia_analiza_reporte_y_lo_incluye_en_pdf(client, login, gemini_falso):
    h = login("coord")
    r = client.get("/reportes/analisis?tipo=citaciones", headers=h)
    assert r.status_code == 200 and r.json()["analisis"].startswith("•")
    pdf = client.get("/reportes/exportar?tipo=citaciones&formato=pdf&analisis=true", headers=h)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    datos_enviados = json.dumps(gemini_falso[-1], ensure_ascii=False)
    assert "Reporte de citaciones" in datos_enviados
