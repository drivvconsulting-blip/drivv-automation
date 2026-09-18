"""Genera el reporte HTML semanal de un cliente a partir del historial en Sheets,
reusando el sistema visual de marca DRIVV (reporte_template.html).

Uso:
  python generar_reporte.py --cliente cristallia-demo
  python generar_reporte.py --todos-los-activos
"""
import argparse
import json
import os
import sys
from math import pi
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # para import sheets_helper
import sheets_helper

TEMPLATE = Path(__file__).parent / "reporte_template.html"
REPORTES_DIR = Path(__file__).parent / "reportes"
CLIENTES_DIR = Path(__file__).parent / "clientes"

SHEET_NAME = "DRIVV Monitoreo"
RADIO = 32
CIRCUNFERENCIA = round(2 * pi * RADIO, 1)  # 201.1

# Índices de columna en la planilla "DRIVV Monitoreo" (ver HEADERS en run_chequeo.py)
COL_FECHA, COL_HORA, COL_CLIENTE, COL_URL, COL_HTTP, COL_OK, COL_CARGA, \
    COL_ERR_N, COL_ERR_DET, COL_EL_N, COL_EL_OK, COL_EL_FAIL, COL_EL_FAIL_DET, \
    COL_SEMAFORO, COL_NOTA = range(15)


def _cargar_config(cliente_id):
    return json.loads((CLIENTES_DIR / f"{cliente_id}.json").read_text(encoding="utf-8"))


def _clientes_activos():
    for f in sorted(CLIENTES_DIR.glob("*.json")):
        if f.name.startswith("_"):
            continue
        c = json.loads(f.read_text(encoding="utf-8"))
        if c.get("activo"):
            yield c["cliente_id"]


def _anillo_svg(color_var, valor_pct):
    offset = round(CIRCUNFERENCIA * (1 - valor_pct / 100), 1)
    color = {"r": "#EF4444", "y": "#F59E0B", "g": "#16A34A"}[color_var]
    color_bg = {"r": "rgba(239,68,68,.15)", "y": "rgba(245,158,11,.15)", "g": "rgba(22,163,74,.15)"}[color_var]
    return f"""<svg width="80" height="80" viewBox="0 0 80 80">
        <circle cx="40" cy="40" r="{RADIO}" fill="none" stroke="{color_bg}" stroke-width="6"/>
        <circle cx="40" cy="40" r="{RADIO}" fill="none" stroke="{color}" stroke-width="6"
          stroke-dasharray="{CIRCUNFERENCIA}" stroke-dashoffset="{offset}" stroke-linecap="round"/>
      </svg>"""


def _gauge_card(estado, nombre, numero, nota):
    """estado: 'r'/'y'/'g'. numero: texto corto a mostrar en el centro del anillo."""
    s_class = {"r": "s-red", "y": "s-yellow", "g": "s-green"}[estado]
    valor_pct = {"r": 20, "y": 60, "g": 100}[estado]
    return f"""      <div class="gauge-card {s_class}">
        <div class="gauge-wrap">
          {_anillo_svg(estado, valor_pct)}
          <div class="gauge-center"><span class="gauge-num {estado}">{numero}</span></div>
        </div>
        <div class="gauge-name">{nombre}</div>
        <div class="gauge-note">{nota}</div>
      </div>"""


def _armar_gauges(fila, config):
    http_ok = fila[COL_OK] == "True"
    http_status = fila[COL_HTTP] or "—"
    g1 = _gauge_card("g" if http_ok else "r", "Disponibilidad", http_status,
                      "Sitio respondió correctamente" if http_ok else "El sitio no respondió bien")

    carga_ms = int(fila[COL_CARGA]) if fila[COL_CARGA] else None
    umbral = config.get("umbral_tiempo_carga_ms", 5000)
    if carga_ms is None:
        estado_carga, nota_carga = "r", "Sin datos de tiempo de carga"
    elif carga_ms <= umbral:
        estado_carga, nota_carga = "g", f"Bajo el umbral de {umbral/1000:.1f}s"
    elif carga_ms <= umbral * 1.5:
        estado_carga, nota_carga = "y", f"Sobre el umbral de {umbral/1000:.1f}s"
    else:
        estado_carga, nota_carga = "r", f"Muy por sobre el umbral de {umbral/1000:.1f}s"
    g2 = _gauge_card(estado_carga, "Tiempo de carga",
                      f"{carga_ms/1000:.1f}s" if carga_ms is not None else "—", nota_carga)

    el_total = int(fila[COL_EL_N] or 0)
    el_fail = int(fila[COL_EL_FAIL] or 0)
    fail_detalle = fila[COL_EL_FAIL_DET]
    requeridos_faltantes = any(
        e["requerido"] for e in config.get("elementos_criticos", [])
        if e["nombre"] in (fail_detalle.split(" | ") if fail_detalle else [])
    )
    if el_fail == 0:
        estado_el, nota_el = "g", "Todos los elementos presentes"
    elif requeridos_faltantes:
        estado_el, nota_el = "r", f"Falta: {fail_detalle}"
    else:
        estado_el, nota_el = "y", f"Falta: {fail_detalle}"
    g3 = _gauge_card(estado_el, "Elementos críticos", f"{el_total - el_fail}/{el_total}", nota_el)

    err_n = int(fila[COL_ERR_N] or 0)
    if err_n == 0:
        estado_err, nota_err = "g", "Sin errores"
    elif err_n <= 2:
        estado_err, nota_err = "y", "Errores menores en consola"
    else:
        estado_err, nota_err = "r", "Varios errores en consola"
    g4 = _gauge_card(estado_err, "Errores de consola", str(err_n), nota_err)

    return "\n".join([g1, g2, g3, g4])


def _armar_findings(fila):
    findings = []
    fail_detalle = fila[COL_EL_FAIL_DET]
    if fail_detalle:
        findings.append(f"""      <div class="finding f-red">
        <div class="finding-head">
          <div class="finding-icon r">⚠</div>
          <div class="finding-title">Elementos críticos no encontrados<small>{fail_detalle}</small></div>
          <span class="finding-badge r">Crítico</span>
        </div>
      </div>""")
    err_det = fila[COL_ERR_DET]
    if err_det:
        findings.append(f"""      <div class="finding f-yellow">
        <div class="finding-head">
          <div class="finding-icon y">⚠</div>
          <div class="finding-title">Errores de consola detectados<small>{err_det}</small></div>
          <span class="finding-badge y">Revisar</span>
        </div>
      </div>""")
    nota = fila[COL_NOTA]
    if nota:
        findings.append(f"""      <div class="finding f-red">
        <div class="finding-head">
          <div class="finding-icon r">✕</div>
          <div class="finding-title">El chequeo no pudo completarse<small>{nota}</small></div>
          <span class="finding-badge r">Crítico</span>
        </div>
      </div>""")
    if not findings:
        findings.append("""      <div class="finding f-green">
        <div class="finding-head">
          <div class="finding-icon g">✓</div>
          <div class="finding-title">Todo funcionando correctamente esta semana</div>
          <span class="finding-badge g">OK</span>
        </div>
      </div>""")
    return "\n".join(findings)


def _armar_historial(filas):
    rows = []
    for f in reversed(filas):
        carga = f"{int(f[COL_CARGA])/1000:.1f}s" if f[COL_CARGA] else "—"
        rows.append(f"""          <tr>
            <td>{f[COL_FECHA]} {f[COL_HORA]}</td>
            <td>{f[COL_HTTP] or '—'}</td>
            <td>{carga}</td>
            <td>{f[COL_ERR_N]}</td>
            <td>{f[COL_EL_OK]}/{f[COL_EL_N]}</td>
            <td><span class="pill {f[COL_SEMAFORO]}">{f[COL_SEMAFORO]}</span></td>
          </tr>""")
    return "\n".join(rows)


SEMAFORO_LABEL = {"rojo": "Requiere atención", "amarillo": "Con observaciones", "verde": "Todo en orden"}


def generar(cliente_id, sheet_id, n_historial=8):
    config = _cargar_config(cliente_id)
    filas = sheets_helper.leer_filas_genericas(sheet_id, "A2:O5000")
    # la API de Sheets recorta las celdas vacías al final de cada fila (ej. si "Nota"
    # quedó vacía), así que hay que rellenar antes de indexar por columna
    filas = [f + [""] * (15 - len(f)) for f in filas if f]
    filas_cliente = [f for f in filas if f[COL_CLIENTE] == cliente_id][-n_historial:]
    if not filas_cliente:
        raise RuntimeError(f"Sin historial todavía para {cliente_id} — corré run_chequeo.py primero.")

    ultima = filas_cliente[-1]
    html = TEMPLATE.read_text(encoding="utf-8")
    html = (html
            .replace("{{CLIENTE_NOMBRE}}", config["nombre"])
            .replace("{{URL}}", config["url"])
            .replace("{{FECHA}}", datetime.now().strftime("%d/%m/%Y"))
            .replace("{{SEMAFORO_GENERAL_LABEL}}", SEMAFORO_LABEL[ultima[COL_SEMAFORO]])
            .replace("{{SEMAFORO_GENERAL}}", ultima[COL_SEMAFORO])
            .replace("{{GAUGES}}", _armar_gauges(ultima, config))
            .replace("{{FINDINGS}}", _armar_findings(ultima))
            .replace("{{HISTORIAL}}", _armar_historial(filas_cliente)))

    REPORTES_DIR.mkdir(exist_ok=True)
    out = REPORTES_DIR / f"{cliente_id}-{datetime.now().strftime('%Y-%m-%d')}.html"
    out.write_text(html, encoding="utf-8")
    print(f"Reporte generado: {out}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--cliente", help="Genera el reporte de un solo cliente")
    g.add_argument("--todos-los-activos", action="store_true", help="Genera el reporte de todos los clientes activos")
    args = ap.parse_args()

    folder_id = os.environ["MONITOREO_DRIVE_FOLDER_ID"]
    sheet_id = sheets_helper.obtener_o_crear_planilla_generica(
        folder_id, SHEET_NAME,
        ["Fecha", "Hora", "Cliente", "URL", "HTTP Status", "OK Status", "Tiempo Carga (ms)",
         "Errores Consola", "Detalle Errores Consola", "Elementos Chequeados", "Elementos OK",
         "Elementos Fallidos", "Detalle Elementos Fallidos", "Semaforo", "Nota"])

    if args.cliente:
        generar(args.cliente, sheet_id)
    else:
        for cid in _clientes_activos():
            generar(cid, sheet_id)
