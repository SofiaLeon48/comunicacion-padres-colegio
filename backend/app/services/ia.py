"""
Inteligencia artificial con Google Gemini (API gratuita de Google AI Studio).

Se usa para:
  - redactar comunicados a partir de una idea corta del docente o coordinación;
  - analizar los datos de un reporte y escribir conclusiones y recomendaciones.

Si GEMINI_API_KEY no está configurada, las funciones de IA responden 503 con un
mensaje claro y el resto de la plataforma sigue funcionando.
"""
import json
import logging

import httpx
from fastapi import HTTPException

from app.core.config import settings

log = logging.getLogger("ia")
URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"


def ia_habilitada() -> bool:
    return bool(settings.GEMINI_API_KEY)


def generar(prompt: str, como_json: bool = False, temperatura: float = 0.6) -> str:
    """Envía el prompt a Gemini y devuelve el texto de la respuesta."""
    if not ia_habilitada():
        raise HTTPException(status_code=503, detail="La IA no está configurada (falta GEMINI_API_KEY en el servidor).")
    cuerpo = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        # Gemini 3.x: se deja la temperatura por defecto (bajarla degrada las respuestas)
        # y se usa razonamiento "low" para que responda rápido.
        "generationConfig": {"thinkingConfig": {"thinkingLevel": "low"}},
    }
    if como_json:
        cuerpo["generationConfig"]["responseMimeType"] = "application/json"
    try:
        r = httpx.post(URL.format(modelo=settings.GEMINI_MODEL), json=cuerpo, timeout=90,
                       headers={"x-goog-api-key": settings.GEMINI_API_KEY})
        r.raise_for_status()
        datos = r.json()
        return "".join(p.get("text", "") for p in datos["candidates"][0]["content"]["parts"]).strip()
    except httpx.HTTPStatusError as e:
        log.warning("Gemini respondió %s: %s", e.response.status_code, e.response.text[:300])
        raise HTTPException(status_code=502, detail="El servicio de IA no respondió correctamente. Intenta de nuevo.")
    except (httpx.HTTPError, KeyError, IndexError) as e:
        log.warning("Error al consultar Gemini: %s", e)
        raise HTTPException(status_code=502, detail="No fue posible comunicarse con el servicio de IA.")


def redactar_comunicado(idea: str, tono: str, destinatarios: str) -> dict:
    prompt = f"""Eres el área de comunicaciones de un colegio en Colombia. Redacta una circular
para los padres de familia y acudientes, en español de Colombia, con tono {tono}.
Destinatarios: {destinatarios}.
Idea principal: {idea}

Reglas: título de máximo 120 caracteres; contenido de 60 a 180 palabras, en párrafos cortos,
con fecha, hora y lugar solo si la idea los menciona (no inventes datos); cierra con un saludo
cordial firmado por "Coordinación". No uses markdown.
Responde SOLO con JSON: {{"titulo": "...", "contenido": "..."}}"""
    texto = generar(prompt, como_json=True, temperatura=0.7)
    try:
        datos = json.loads(texto)
        return {"titulo": str(datos["titulo"])[:150], "contenido": str(datos["contenido"]).strip()}
    except (json.JSONDecodeError, KeyError, TypeError):
        raise HTTPException(status_code=502, detail="La IA devolvió una respuesta inesperada. Intenta de nuevo.")


def analizar_reporte(titulo: str, criterios: str, resumen: dict, filas: list[dict]) -> str:
    muestra = filas[:60]   # suficiente contexto sin exceder el límite del modelo
    prompt = f"""Eres analista de convivencia y comunicación de un colegio en Colombia.
Analiza el reporte "{titulo}" ({criterios}).
Resumen: {json.dumps(resumen, ensure_ascii=False, default=str)}
Registros (máximo 60): {json.dumps(muestra, ensure_ascii=False, default=str)}

Escribe en español, sin markdown, entre 4 y 6 viñetas que empiecen con "• ":
hallazgos clave con cifras, grupos o casos que requieren atención y 2 recomendaciones
concretas para coordinación. No inventes datos que no estén en el reporte."""
    return generar(prompt, temperatura=0.4)
