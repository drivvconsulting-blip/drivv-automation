import os
import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

REMITENTE = "drivvconsulting@gmail.com"
NOMBRE_REMIT = "Lukas Geissbuhler — DRIVV Consultoria Digital"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
TEMPLATE_PATH = Path(__file__).parent / "email-template-prospeccion.html"

def armar_html(empresa, hallazgo, pitch):
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return (template
            .replace("{{EMPRESA}}", empresa)
            .replace("{{HALLAZGO}}", hallazgo)
            .replace("{{PITCH}}", pitch))

def enviar_correo(destinatario, asunto, html):
    password = os.environ["GMAIL_APP_PASSWORD"]
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{NOMBRE_REMIT} <{REMITENTE}>"
    msg["To"] = destinatario
    msg["Subject"] = asunto
    msg["Reply-To"] = REMITENTE
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as srv:
        srv.login(REMITENTE, password)
        srv.sendmail(REMITENTE, [destinatario], msg.as_string())
