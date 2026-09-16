# DRIVV — Automatización de prospección

Herramientas reutilizables para el agente de prospección de DRIVV Consultoría Digital: verificar el sitio de un prospecto (Firecrawl), registrar prospectos en Google Sheets, y enviar el correo de prospección con la plantilla oficial.

## Variables de entorno necesarias

- `FIRECRAWL_API_KEY` — API key del plan gratis de firecrawl.dev
- `SERVICE_ACCOUNT_JSON` — contenido completo del JSON de la cuenta de servicio de Google (como texto), no una ruta de archivo
- `DRIVE_FOLDER_ID` — ID de la carpeta de Drive "DRIVV Prospectos" (opcional, tiene un valor por defecto)
- `GMAIL_APP_PASSWORD` — contraseña de aplicación de Gmail para drivvconsulting@gmail.com

Ninguna credencial va escrita en este repositorio.

## Módulos

- `verificar_prospecto.py` — `verificar(url)`: analiza un sitio con Firecrawl y devuelve señales (blog, reseñas, ubicación).
- `sheets_helper.py` — `obtener_o_crear_planilla()`, `emails_ya_registrados(sheet_id)`, `agregar_prospectos(sheet_id, filas)`.
- `enviar_correo.py` — `armar_html(empresa, hallazgo, pitch)`, `enviar_correo(destinatario, asunto, html)`.

## Reglas de negocio (ver memoria de DRIVV para el detalle completo)

- Nunca mencionar "IA" en los correos.
- El hallazgo debe ser real y verificado con `verificar_prospecto.py`, nunca genérico o inventado.
- Solo prospectos con oportunidad alta o media, ubicados en Santiago, Chile.
- Sin botón en el correo — el CTA es responder o agendar una llamada de 20 minutos.
- Incluir línea de opt-out en el pie del correo.
- Horario de envío: lunes a viernes, 8:00–13:00 hora de Chile.
