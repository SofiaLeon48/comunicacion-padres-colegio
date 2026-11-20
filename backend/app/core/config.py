"""
Configuración central de la aplicación.

Todas las variables sensibles (credenciales, llaves) se leen del archivo .env
y NUNCA se escriben directamente en el código.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Cadena de conexión que entrega Neon (Dashboard → Connection string)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # Zona horaria del colegio (fechas de citaciones, "ahora")
    ZONA_HORARIA: str = os.getenv("ZONA_HORARIA", "America/Bogota")

    # Seguridad (JWT)
    JWT_SECRET: str = os.getenv("JWT_SECRET", "cambia-esta-clave-en-produccion")
    JWT_ALGORITMO: str = "HS256"
    JWT_EXPIRA_MINUTOS: int = int(os.getenv("JWT_EXPIRA_MINUTOS", "480"))  # 8 horas

    # Orígenes permitidos para el frontend (Svelte). Separados por coma.
    CORS_ORIGINS: list[str] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
        if o.strip()
    ]

    # Además se acepta cualquier subdominio que cumpla esta expresión (p. ej. despliegues de Vercel)
    # La app móvil (Capacitor) llama desde https://localhost o capacitor://localhost.
    CORS_ORIGIN_REGEX: str = os.getenv(
        "CORS_ORIGIN_REGEX", r"(https://.*\.vercel\.app|https?://localhost|capacitor://localhost)")

    # Correo (opcional). Si SMTP_HOST está vacío, no se envían correos.
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_REMITENTE: str = os.getenv("SMTP_REMITENTE", "")

    # Correo por API con Brevo (recomendado en Render, que bloquea SMTP en el plan gratis).
    # Si BREVO_API_KEY tiene valor, se usa Brevo en lugar de SMTP.
    BREVO_API_KEY: str = os.getenv("BREVO_API_KEY", "")
    CORREO_REMITENTE: str = os.getenv("CORREO_REMITENTE", os.getenv("SMTP_REMITENTE", ""))
    CORREO_REMITENTE_NOMBRE: str = os.getenv("CORREO_REMITENTE_NOMBRE", "Conecta Escolar")

    # Inteligencia artificial (Google Gemini). Sin llave, las funciones de IA quedan desactivadas.
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Tablero publicado: llave del enlace público (iframe). Si está vacía se deriva de JWT_SECRET.
    TABLERO_TOKEN: str = os.getenv("TABLERO_TOKEN", "")


settings = Settings()


def ahora_local():
    """Fecha y hora actual en la zona del colegio, sin tzinfo (igual que TIMESTAMP en la BD)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo(settings.ZONA_HORARIA)).replace(tzinfo=None)


def a_hora_local(dt):
    """Si una fecha llega con zona horaria (ej. ...Z), se convierte a hora local sin tzinfo."""
    from zoneinfo import ZoneInfo
    if dt is not None and dt.tzinfo is not None:
        return dt.astimezone(ZoneInfo(settings.ZONA_HORARIA)).replace(tzinfo=None)
    return dt
