"""Pasa los precios de Vendita a productos.json de la tienda (corre una vez por noche desde la PC).

Uso:
    python herramientas/precios_desde_vendita.py EXPORT_VENDITA.xlsx productos.json [STOCK_FREEWILD.json]

- EXPORT_VENDITA.xlsx: Productos > Stock por Sucursal > Casa Central > Exportar a Excel
  (Código, Nombre, Rubro, Proveedor, Marca, Costo, Precio de venta, Stock).
- productos.json: solo se cambia el precio de los productos que ya están en la tienda. Nombres, rubros,
  fotos y productos nuevos no se tocan. Nunca se escriben costos ni stock acá (el repositorio es público).
- STOCK_FREEWILD.json (opcional, privado, NUNCA en este repositorio): stock, costo y precio de cada producto
  partido en pedazos para cargarlo en la ventana Administración de Freewild.

Protecciones: no se usa un precio de Vendita de $10 o menos (precios basura como $2), ni uno que baje a
menos de la mitad o suba a más del triple del precio que tiene hoy la tienda. Esos quedan listados para revisar.
"""
import json
import math
import sys
import unicodedata
from datetime import datetime

import pandas as pd

PARTE_MAX = 200_000  # bytes por documento de Freewild (el límite es 256 KiB)


def _norm(s):
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower()
    return " ".join(s.replace(".", " ").split())


def _col(cols, *opciones):
    n = {_norm(c): c for c in cols}
    for o in opciones:
        if o in n:
            return n[o]
    for o in opciones:
        for k, c in n.items():
            if k.startswith(o):
                return c
    return None


def _num(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    t = str(v).replace("$", "").replace(" ", "").strip()
    if not t:
        return None
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def leer_vendita(path):
    df = pd.read_excel(path, dtype=str)
    cols = list(df.columns)
    c_cod = _col(cols, "codigo", "cod")
    c_nom = _col(cols, "nombre", "descripcion", "producto")
    c_pre = _col(cols, "precio de venta", "precio venta", "precio")
    c_cos = _col(cols, "costo", "precio de compra")
    c_stk = _col(cols, "stock")
    if not c_cod or not c_pre:
        sys.exit(f"No encuentro las columnas de código y precio en {path}. Columnas: {cols}")
    filas = []
    for _, r in df.iterrows():
        ean = str(r[c_cod] or "").strip()
        if not ean or ean.lower() == "nan":
            continue
        if ean.endswith(".0"):
            ean = ean[:-2]
        filas.append({
            "ean": ean,
            "nombre": str(r[c_nom]).strip() if c_nom else "",
            "precio": _num(r[c_pre]),
            "costo": _num(r[c_cos]) if c_cos else None,
            "stock": _num(r[c_stk]) if c_stk else None,
        })
    return filas


def main(export, productos_path, stock_path=None):
    filas = leer_vendita(export)
    ven = {f["ean"]: f for f in filas}
    with open(productos_path, encoding="utf-8") as f:
        tienda = json.load(f)

    cambiados, revisar, iguales, sin_vendita = [], [], 0, 0
    for p in tienda["p"]:
        v = ven.get(p[0])
        if not v or v["precio"] is None:
            sin_vendita += 1
            continue
        nuevo = int(math.ceil(v["precio"] - 1e-6))
        actual = p[3]
        if nuevo == actual:
            iguales += 1
            continue
        if nuevo <= 10 or (actual and (nuevo < actual / 2 or nuevo > actual * 3)):
            revisar.append((p[0], p[1], actual, nuevo))
            continue
        cambiados.append((p[0], p[1], actual, nuevo))
        p[3] = nuevo

    with open(productos_path, "w", encoding="utf-8") as f:
        json.dump(tienda, f, ensure_ascii=False, separators=(",", ":"))

    en_tienda = {p[0] for p in tienda["p"]}
    nuevos_vendita = sum(1 for e in ven if e not in en_tienda)
    print(f"Precios de la tienda: {len(cambiados)} cambiados, {iguales} iguales, "
          f"{len(revisar)} para revisar, {sin_vendita} sin dato en Vendita, "
          f"{nuevos_vendita} productos de Vendita que no están en la tienda.")
    for e, n, a, b in revisar[:50]:
        print(f"  REVISAR {e} | {n} | tienda ${a} | Vendita ${b}")

    if stock_path:
        def f(x):
            return "" if x is None else (str(int(x)) if float(x).is_integer() else f"{x:.2f}")
        lineas = [f"{x['ean']}|{f(x['stock'])}|{f(x['costo'])}|{f(x['precio'])}|{x['nombre'].replace('|', '/')}"
                  for x in filas]
        partes, cur, tam = [], [], 0
        for l in lineas:
            b = len(l.encode("utf-8")) + 1
            if cur and tam + b > PARTE_MAX:
                partes.append("\n".join(cur))
                cur, tam = [], 0
            cur.append(l)
            tam += b
        if cur:
            partes.append("\n".join(cur))
        with open(stock_path, "w", encoding="utf-8") as fh:
            json.dump({"fecha": datetime.now().strftime("%d/%m %H:%M"), "productos": len(lineas),
                       "partes": partes}, fh, ensure_ascii=False)
        print(f"Stock para Freewild: {len(lineas)} productos en {len(partes)} partes -> {stock_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(*sys.argv[1:4])
