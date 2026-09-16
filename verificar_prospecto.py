import os
import sys
import re
import requests

FIRECRAWL_KEY = os.environ["FIRECRAWL_API_KEY"]

def verificar(url):
    resp = requests.post(
        "https://api.firecrawl.dev/v1/scrape",
        headers={"Authorization": f"Bearer {FIRECRAWL_KEY}", "Content-Type": "application/json"},
        json={"url": url, "formats": ["markdown"], "onlyMainContent": True},
        timeout=30
    )
    if resp.status_code != 200:
        print(f"[HTTP {resp.status_code}] {url}: {resp.text[:300]}")
        return None
    data = resp.json()
    if not data.get("success"):
        print(f"[ERROR] {url}: {data}")
        return None
    md = data["data"].get("markdown", "")
    meta = data["data"].get("metadata", {})

    emails = sorted(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", md)))
    tiene_blog = bool(re.search(r"\b(blog|noticias|art[ií]culos)\b", md, re.I))
    tiene_resenas = bool(re.search(r"\b(rese[ñn]as|opiniones|testimonios|clientes dicen)\b", md, re.I))
    tiene_direccion = bool(re.search(r"\b(santiago|providencia|nu[ñn]oa|las condes|maip[uú]|estaci[oó]n central)\b", md, re.I))

    print(f"\n{'='*70}\n{url}\n{'='*70}")
    print(f"Titulo: {meta.get('title')}")
    print(f"Largo contenido: {len(md)} caracteres")
    print(f"Emails encontrados: {emails}")
    print(f"Tiene blog/noticias: {tiene_blog}")
    print(f"Tiene resenas/testimonios visibles: {tiene_resenas}")
    print(f"Menciona ubicacion Santiago/comuna: {tiene_direccion}")
    return {"url": url, "meta": meta, "emails": emails, "tiene_blog": tiene_blog,
            "tiene_resenas": tiene_resenas, "tiene_direccion": tiene_direccion, "largo": len(md)}

if __name__ == "__main__":
    for url in sys.argv[1:]:
        verificar(url)
