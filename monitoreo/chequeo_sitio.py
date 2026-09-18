"""Chequeo de salud técnica de un sitio cliente, vía Playwright headless.
Uso: python chequeo_sitio.py --cliente <cliente_id>
"""
import argparse
import json
import time
from pathlib import Path
from datetime import datetime

from playwright.sync_api import sync_playwright

CLIENTES_DIR = Path(__file__).parent / "clientes"


def cargar_config(cliente_id):
    return json.loads((CLIENTES_DIR / f"{cliente_id}.json").read_text(encoding="utf-8"))


def chequear(config):
    resultado = {
        "cliente": config["cliente_id"],
        "url": config["url"],
        "http_status": None,
        "ok_status": False,
        "tiempo_carga_ms": None,
        "errores_consola": [],
        "elementos": [],
        "nota": "",
    }
    errores = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("console", lambda m: errores.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errores.append(str(e)))
        try:
            t0 = time.monotonic()
            resp = page.goto(config["url"], timeout=config.get("timeout_ms", 15000), wait_until="load")
            resultado["tiempo_carga_ms"] = round((time.monotonic() - t0) * 1000)
            resultado["http_status"] = resp.status if resp else None
            resultado["ok_status"] = bool(resp) and resp.status < 400
            for el in config.get("elementos_criticos", []):
                encontrado = page.locator(el["selector"]).count() > 0
                resultado["elementos"].append({**el, "encontrado": encontrado})
        except Exception as e:
            resultado["nota"] = f"Excepción durante chequeo: {e}"
        finally:
            resultado["errores_consola"] = errores
            browser.close()
    resultado["semaforo"] = _calcular_semaforo(resultado, config)
    return resultado


def _calcular_semaforo(r, config):
    if r["nota"] or not r["ok_status"]:
        return "rojo"
    if any(e["requerido"] and not e["encontrado"] for e in r["elementos"]):
        return "rojo"
    umbral = config.get("umbral_tiempo_carga_ms", 5000)
    if r["tiempo_carga_ms"] and r["tiempo_carga_ms"] > umbral:
        return "amarillo"
    if r["errores_consola"] or any(not e["encontrado"] for e in r["elementos"]):
        return "amarillo"
    return "verde"


def resultado_a_fila(r):
    ok = [e for e in r["elementos"] if e["encontrado"]]
    fail = [e for e in r["elementos"] if not e["encontrado"]]
    ahora = datetime.now()
    return [
        ahora.strftime("%Y-%m-%d"), ahora.strftime("%H:%M"), r["cliente"], r["url"],
        str(r["http_status"] or ""), str(r["ok_status"]), str(r["tiempo_carga_ms"] or ""),
        str(len(r["errores_consola"])), " | ".join(r["errores_consola"][:5]),
        str(len(r["elementos"])), str(len(ok)), str(len(fail)),
        " | ".join(e["nombre"] for e in fail), r["semaforo"], r["nota"],
    ]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cliente", required=True)
    args = ap.parse_args()
    resultado = chequear(cargar_config(args.cliente))
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
