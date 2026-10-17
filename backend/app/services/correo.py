"""
Envío de correos (opcional).

Si SMTP_HOST no está configurado en el .env, simplemente no se envía nada y la
notificación queda solo dentro de la plataforma. Con Gmail se usa
SMTP_HOST=smtp.gmail.com, SMTP_PORT=587 y una "contraseña de aplicación".
"""
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

log = logging.getLogger("correo")


def correo_habilitado() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_REMITENTE)


def enviar_correo(destinatarios: list[str], asunto: str, cuerpo: str) -> bool:
    if not correo_habilitado() or not destinatarios:
        return False
    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = settings.SMTP_REMITENTE
    msg["To"] = settings.SMTP_REMITENTE
    msg["Bcc"] = ", ".join(destinatarios)          # copia oculta: nadie ve los correos de los demás
    msg.set_content(cuerpo)
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            smtp.starttls()
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:  # el correo nunca debe tumbar la API
        log.warning("No se pudo enviar el correo: %s", e)
        return False
