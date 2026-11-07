"""Filtra candidatos de prospeccion contra TODA la planilla antes de enviar.

Uso:
    python3 filtrar_contactados.py candidatos.json

candidatos.json = lista de objetos con al menos {"nombre": ..., "email": ...}.
Imprime cada candidato como NUEVO o REPETIDO (con el motivo) y escribe
candidatos_nuevos.json solo con los que se pueden contactar. Tambien descarta
repetidos dentro de la misma lista.
"""
import json
import sys

import sheets_helper as sh


def main(ruta):
    candidatos = json.load(open(ruta, encoding="utf-8"))
    sheet_id = sh.obtener_o_crear_planilla()
    filas = sh.leer_filas(sheet_id)
    nuevos, vistos = [], []
    for c in candidatos:
        motivo = sh.ya_contactado(sheet_id, c.get("email", ""), c.get("nombre", ""), filas=filas)
        if not motivo:
            falsa = [["", "", v.get("nombre", ""), v.get("email", ""), "", "", "", "candidato de hoy", "", "hoy"] for v in vistos]
            motivo = sh.ya_contactado(sheet_id, c.get("email", ""), c.get("nombre", ""), filas=falsa)
        if motivo:
            print(f"REPETIDO  {c.get('nombre')} <{c.get('email')}>: {motivo}")
        else:
            print(f"NUEVO     {c.get('nombre')} <{c.get('email')}>")
            nuevos.append(c)
            vistos.append(c)
    json.dump(nuevos, open("candidatos_nuevos.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n{len(nuevos)} nuevos de {len(candidatos)} candidatos -> candidatos_nuevos.json")


if __name__ == "__main__":
    main(sys.argv[1])
