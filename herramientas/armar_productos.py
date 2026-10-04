"""Arma productos.json de la tienda cruzando por EAN la lista de precios con la lista maestra de nombres.

Uso:
    python3 herramientas/armar_productos.py LISTA_PRECIOS.xlsx MAESTRO.csv productos.json

- LISTA_PRECIOS.xlsx: export de precios del súper (hoja "Precios" con columnas EAN, Descripción, Rubro,
  "Precio Venta Final (C/IVA)"). Tiene costos, así que NO va en este repositorio.
- MAESTRO.csv: ean, nombre_sag, nombre_tienda, rubro, subcategoria, gramos_por_toque (vacío = por unidad).
  El nombre y la subcategoría salen de acá; el precio siempre sale de la lista de precios.
- Un EAN nuevo que no está en el maestro sale con el nombre de SAG hasta que se le asigne uno.
"""
import csv
import json
import math
import os
import sys

import pandas as pd

EXCLUIR_RUBROS = {"Cigarrillos", "Combos/Promociones internas", "SIN CLASIFICAR"}


def main(lista, maestro_path, salida):
    precios = pd.read_excel(lista, sheet_name="Precios", dtype={"EAN": str})
    maestro = {}
    with open(maestro_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            maestro[row["ean"]] = row

    rubros, subs, productos = [], [], []
    for _, r in precios.iterrows():
        ean = str(r["EAN"]).strip()
        rubro = str(r["Rubro"]).strip()
        precio = r["Precio Venta Final (C/IVA)"]
        if rubro in EXCLUIR_RUBROS or not precio or precio <= 0:
            continue
        m = maestro.get(ean, {})
        # El rubro corregido de la lista maestra manda sobre el de SAG (hay productos mal cargados).
        rubro = (m.get("rubro") or "").strip() or rubro
        if rubro not in rubros:
            rubros.append(rubro)
        sub = (m.get("subcategoria") or "").strip()
        if sub and sub not in subs:
            subs.append(sub)
        nombre_sag = str(r["Descripción"]).strip()
        nombre = (m.get("nombre_tienda") or "").strip()
        gramos = int(m["gramos_por_toque"]) if (m.get("gramos_por_toque") or "").strip() else 0
        # [ean, nombre, rubro, precio, gramos_por_toque, subcategoria, nombre_sag (solo si hay nombre nuevo)]
        productos.append([ean, nombre or nombre_sag, 0, int(math.ceil(precio)), gramos,
                          subs.index(sub) if sub else -1, nombre_sag if nombre else ""])
        productos[-1][2] = rubro

    rubros.sort()
    subs_ordenadas = sorted(subs)
    for p in productos:
        p[2] = rubros.index(p[2])
        if p[5] >= 0:
            p[5] = subs_ordenadas.index(subs[p[5]])
    productos.sort(key=lambda p: p[1].lower())
    # "f": productos con foto en fotos/<EAN>.jpg (carpeta al lado de productos.json).
    carpeta = os.path.join(os.path.dirname(os.path.abspath(salida)), "fotos")
    hay = {n[:-4] for n in os.listdir(carpeta) if n.endswith(".jpg")} if os.path.isdir(carpeta) else set()
    con_foto = sorted(p[0] for p in productos if p[0] in hay)
    with open(salida, "w", encoding="utf-8") as f:
        json.dump({"r": rubros, "s": subs_ordenadas, "p": productos, "f": con_foto}, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(productos)} productos, {len(rubros)} rubros, {len(subs_ordenadas)} subcategorías")


if __name__ == "__main__":
    main(*sys.argv[1:4])
