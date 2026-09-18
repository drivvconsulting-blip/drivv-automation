# DRIVV — Automatización de prospección y monitoreo

Herramientas reutilizables para DRIVV Consultoría Digital: el agente de prospección (verificar el sitio de un prospecto con Firecrawl, registrar en Sheets, enviar el correo con la plantilla oficial) y el retainer de monitoreo mensual de clientes (`monitoreo/`).

## Variables de entorno necesarias

- `FIRECRAWL_API_KEY` — API key del plan gratis de firecrawl.dev
- `SERVICE_ACCOUNT_JSON` — contenido completo del JSON de la cuenta de servicio de Google (como texto), no una ruta de archivo
- `DRIVE_FOLDER_ID` — ID de la carpeta de Drive "DRIVV Prospectos" (opcional, tiene un valor por defecto)
- `GMAIL_APP_PASSWORD` — contraseña de aplicación de Gmail para drivvconsulting@gmail.com
- `MONITOREO_DRIVE_FOLDER_ID` — ID de la carpeta de Drive "DRIVV Monitoreo" (solo para `monitoreo/`)

Ninguna credencial va escrita en este repositorio.

## Módulos de prospección

- `verificar_prospecto.py` — `verificar(url)`: analiza un sitio con Firecrawl y devuelve señales (blog, reseñas, ubicación).
- `sheets_helper.py` — `obtener_o_crear_planilla()`, `emails_ya_registrados(sheet_id)`, `agregar_prospectos(sheet_id, filas)`. También trae funciones genéricas (`obtener_o_crear_planilla_generica`, `agregar_filas_genericas`, `leer_filas_genericas`) usadas por `monitoreo/`.
- `enviar_correo.py` — `armar_html(empresa, hallazgo, pitch)`, `enviar_correo(destinatario, asunto, html)`.

### Reglas de negocio de prospección (ver memoria de DRIVV para el detalle completo)

- Nunca mencionar "IA" en los correos.
- El hallazgo debe ser real y verificado con `verificar_prospecto.py`, nunca genérico o inventado.
- Solo prospectos con oportunidad alta o media, ubicados en Santiago, Chile.
- Sin botón en el correo — el CTA es responder o agendar una llamada de 20 minutos.
- Incluir línea de opt-out en el pie del correo.
- Horario de envío: lunes a viernes, 8:00–13:00 hora de Chile.

## Retainer de monitoreo mensual (`monitoreo/`)

Sistema genérico (sin cliente asignado por defecto) para ofrecer un retainer de monitoreo de salud técnica a clientes cerrados. Corre solo, cada lunes, vía GitHub Actions (`.github/workflows/monitoreo-semanal.yml`) — no depende de que ninguna PC esté encendida.

- `clientes/<cliente_id>.json` — un config por cliente: URL, umbral de tiempo de carga, y selectores CSS de elementos críticos a verificar. `activo:true` lo incluye en la corrida del cron; `activo:false` lo excluye (útil para pruebas, como `cristallia-demo.json`).
- `chequeo_sitio.py` — chequea un sitio con Playwright (librería estándar, headless, sin MCP): status HTTP, tiempo de carga, errores de consola, y presencia de elementos críticos.
- `run_chequeo.py` — corre `chequeo_sitio.py` sobre todos los clientes activos y loguea cada resultado como fila en la planilla "DRIVV Monitoreo". Con `--cliente <id>` corre un cliente puntual aunque esté `activo:false` (para pruebas).
- `generar_reporte.py` — arma el reporte HTML semanal por cliente a partir del historial en Sheets, reusando el CSS de marca DRIVV (`reporte_template.html`, mismas clases que los diagnósticos).

### Onboardear un cliente nuevo al retainer

1. Copiar `clientes/_schema_ejemplo.json` a `clientes/<cliente_id>.json`, completar URL y elementos críticos, y poner `"activo": true`.
2. Confirmar los selectores CSS localmente: `python monitoreo/chequeo_sitio.py --cliente <cliente_id>`.
3. Commitear y pushear — el cron de los lunes lo toma automáticamente.

### Correr localmente

```
SERVICE_ACCOUNT_JSON=... MONITOREO_DRIVE_FOLDER_ID=... python monitoreo/run_chequeo.py --cliente cristallia-demo
SERVICE_ACCOUNT_JSON=... MONITOREO_DRIVE_FOLDER_ID=... python monitoreo/generar_reporte.py --cliente cristallia-demo
```
