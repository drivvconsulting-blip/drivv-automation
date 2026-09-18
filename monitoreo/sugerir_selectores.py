"""Escanea un sitio y sugiere selectores CSS candidatos para 'elementos_criticos'
en un config de monitoreo/clientes/<cliente_id>.json — pensado para usarse al
onboardear un cliente nuevo, cuando no se conocen los selectores exactos del tema.

Uso: python sugerir_selectores.py <url>
"""
import argparse
import re
from playwright.sync_api import sync_playwright

FRASES_CARRITO = re.compile(
    r"agregar al carrito|añadir al carrito|agregar|añadir|comprar ahora|buy now|add to cart",
    re.IGNORECASE,
)
SELECTORES_CARRITO_COMUNES = [
    "button[name='add']",
    ".product-form__submit",
    "[data-add-to-cart]",
    "button[type='submit'][class*='cart']",
    "button[class*='add-to-cart']",
]


def escanear(url, timeout_ms=15000):
    candidatos_carrito = []
    candidatos_forms = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=timeout_ms, wait_until="load")

        for sel in SELECTORES_CARRITO_COMUNES:
            n = page.locator(sel).count()
            if n > 0:
                texto = page.locator(sel).first.inner_text().strip()[:40]
                candidatos_carrito.append((sel, n, texto))

        botones = page.locator("button, a[role='button'], input[type='submit']")
        vistos = set()
        for i in range(min(botones.count(), 60)):
            el = botones.nth(i)
            try:
                texto = el.inner_text().strip()
            except Exception:
                continue
            if texto and FRASES_CARRITO.search(texto) and texto not in vistos:
                vistos.add(texto)
                clase = el.get_attribute("class") or ""
                clase_sel = "." + clase.split()[0] if clase else None
                candidatos_carrito.append((clase_sel or "(sin clase — usar texto)", 1, texto))

        forms = page.locator("form")
        for i in range(forms.count()):
            f = forms.nth(i)
            fid = f.get_attribute("id") or ""
            action = f.get_attribute("action") or ""
            # solo nos interesan formularios que realmente parezcan de contacto —
            # un id cualquiera (selector de pais, carrito) no cuenta
            parece_contacto = (
                "contact" in fid.lower()
                or "contact" in action.lower()
                or (f.locator("input[type='email']").count() > 0
                    and f.locator("textarea").count() > 0)
            )
            if not parece_contacto:
                continue
            if fid:
                sel = f"form#{fid}"
            elif "contact" in action.lower():
                sel = "form[action*='contact']"
            else:
                sel = "form:has(input[type='email']):has(textarea)"
            candidatos_forms.append((sel, action or "(sin action)"))

        browser.close()
    return candidatos_carrito, candidatos_forms


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    args = ap.parse_args()

    print(f"Buscando elementos típicos en {args.url}...\n")
    carrito, forms = escanear(args.url)

    print("Posibles botones de 'agregar al carrito' / compra:")
    if carrito:
        vistos_sel = set()
        for sel, n, texto in carrito:
            if sel in vistos_sel:
                continue
            vistos_sel.add(sel)
            print(f"  - {sel}  ({n} encontrado(s), texto: \"{texto}\")")
    else:
        print("  (nada encontrado automáticamente)")

    print("\nPosibles formularios de contacto:")
    if forms:
        for sel, action in forms:
            print(f"  - {sel}  (action: {action})")
    else:
        print("  (nada encontrado automáticamente)")

    if not carrito and not forms:
        print(
            "\nNo se encontró nada con los patrones comunes. Puede que el sitio use un "
            "patrón no estándar — revisá manualmente con el inspector del navegador "
            "(clic derecho > Inspeccionar) sobre el botón/formulario que querés monitorear."
        )
