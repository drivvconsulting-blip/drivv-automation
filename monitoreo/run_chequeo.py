"""Orquestador del cron de monitoreo: recorre los clientes activos, corre el chequeo
de cada uno y loguea el resultado en Google Sheets.
Uso normal (cron):        python run_chequeo.py
Uso puntual (un cliente,
incluso si activo:false): python run_chequeo.py --cliente cristallia-demo
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # para import sheets_helper
import sheets_helper
import chequeo_sitio

CLIENTES_DIR = Path(__file__).parent / "clientes"
SHEET_NAME = "DRIVV Monitoreo"
HEADERS = [
    "Fecha", "Hora", "Cliente", "URL", "HTTP Status", "OK Status", "Tiempo Carga (ms)",
    "Errores Consola", "Detalle Errores Consola", "Elementos Chequeados", "Elementos OK",
    "Elementos Fallidos", "Detalle Elementos Fallidos", "Semaforo", "Nota",
]


def clientes_activos():
    for f in sorted(CLIENTES_DIR.glob("*.json")):
        if f.name.startswith("_"):
            continue
        c = json.loads(f.read_text(encoding="utf-8"))
        if c.get("activo"):
            yield c


def cargar_cliente(cliente_id):
    return json.loads((CLIENTES_DIR / f"{cliente_id}.json").read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cliente", help="Corre un solo cliente puntualmente, ignorando el filtro activo:true")
    args = ap.parse_args()

    folder_id = os.environ["MONITOREO_DRIVE_FOLDER_ID"]
    sheet_id = sheets_helper.obtener_o_crear_planilla_generica(folder_id, SHEET_NAME, HEADERS)

    configs = [cargar_cliente(args.cliente)] if args.cliente else list(clientes_activos())

    en_rojo = []
    for config in configs:
        r = chequeo_sitio.chequear(config)
        sheets_helper.agregar_filas_genericas(sheet_id, [chequeo_sitio.resultado_a_fila(r)])
        print(f"[{r['semaforo'].upper()}] {r['cliente']} -> HTTP {r['http_status']}, {r['tiempo_carga_ms']}ms")
        if r["semaforo"] == "rojo":
            en_rojo.append(r["cliente"])

    if en_rojo:
        print(f"::warning::Clientes en rojo esta semana: {', '.join(en_rojo)}")


if __name__ == "__main__":
    main()
