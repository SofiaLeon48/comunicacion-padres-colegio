"""
Envío de correos (opcional).

Dos formas, según lo que esté configurado en el .env:
  1. Brevo (recomendado): BREVO_API_KEY + CORREO_REMITENTE. Funciona por HTTPS, así que
     sirve en Render gratis (que bloquea los puertos SMTP).
  2. SMTP clásico: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD y SMTP_REMITENTE.
Si no hay ninguna configurada, no se envía nada y la notificación queda solo en la plataforma.
"""
import base64
import logging
import smtplib
from email.message import EmailMessage

import httpx

from app.core.config import settings

log = logging.getLogger("correo")
BREVO_URL = "https://api.brevo.com/v3/smtp/email"


def correo_habilitado() -> bool:
    return bool((settings.BREVO_API_KEY and settings.CORREO_REMITENTE)
                or (settings.SMTP_HOST and settings.SMTP_REMITENTE))


def _brevo(destinatarios, asunto, cuerpo, html, adjuntos, copia_oculta) -> bool:
    remitente = {"email": settings.CORREO_REMITENTE, "name": settings.CORREO_REMITENTE_NOMBRE}
    datos = {"sender": remitente, "subject": asunto, "textContent": cuerpo}
    if html:
        datos["htmlContent"] = html
    if copia_oculta:   # nadie ve los correos de los demás
        datos["to"] = [{"email": settings.CORREO_REMITENTE}]
        datos["bcc"] = [{"email": d} for d in destinatarios]
    else:
        datos["to"] = [{"email": d} for d in destinatarios]
    if adjuntos:
        datos["attachment"] = [{"name": n, "content": base64.b64encode(c).decode()} for n, c in adjuntos]
    r = httpx.post(BREVO_URL, json=datos, timeout=30,
                   headers={"api-key": settings.BREVO_API_KEY, "accept": "application/json"})
    if r.status_code >= 300:
        log.warning("Brevo respondió %s: %s", r.status_code, r.text[:300])
        return False
    return True


def _smtp(destinatarios, asunto, cuerpo, html, adjuntos, copia_oculta) -> bool:
    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = settings.SMTP_REMITENTE
    if copia_oculta:
        msg["To"] = settings.SMTP_REMITENTE
        msg["Bcc"] = ", ".join(destinatarios)
    else:
        msg["To"] = ", ".join(destinatarios)
    msg.set_content(cuerpo)
    if html:
        msg.add_alternative(html, subtype="html")
    for nombre, contenido in adjuntos or []:
        tipo = ("application", "pdf") if nombre.endswith(".pdf") else \
               ("application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        msg.add_attachment(contenido, maintype=tipo[0], subtype=tipo[1], filename=nombre)
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        smtp.starttls()
        if settings.SMTP_USER:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)
    return True


def enviar_correo(destinatarios: list[str], asunto: str, cuerpo: str, html: str | None = None,
                  adjuntos: list[tuple[str, bytes]] | None = None, copia_oculta: bool = True) -> bool:
    """Devuelve True si el correo salió. Nunca lanza errores: el correo no debe tumbar la API."""
    if not correo_habilitado() or not destinatarios:
        return False
    try:
        if settings.BREVO_API_KEY:
            return _brevo(destinatarios, asunto, cuerpo, html, adjuntos, copia_oculta)
        return _smtp(destinatarios, asunto, cuerpo, html, adjuntos, copia_oculta)
    except Exception as e:
        log.warning("No se pudo enviar el correo: %s", e)
        return False
