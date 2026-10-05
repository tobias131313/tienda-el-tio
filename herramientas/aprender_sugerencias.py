"""Aprende qué productos se compran juntos y lo guarda en sugerencias.json ("a").

La tienda muestra primero lo aprendido y después las reglas a mano (armar_sugerencias.py),
así que con cada pedido nuevo las sugerencias se parecen más a lo que compra la gente del barrio.

Uso:
  python3 herramientas/aprender_sugerencias.py pedidos.json

pedidos.json es una lista de pedidos. Cada pedido trae "items": una lista de códigos (EAN),
o de objetos con "ean" / "codigo" / "nombre". Se ignoran los pedidos con "prueba": true
y los que tengan "estado": "cancelado". Sirve el export del panel o, más adelante, de Firebase.
"""
import json, sys
from collections import Counter
from itertools import combinations
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MIN_JUNTOS = 3   # pedidos mínimos en los que aparecen juntos para confiar en el par
MIN_LIFT = 1.2   # cuánto más se compran juntos que por casualidad
MAX = 6          # sugerencias aprendidas por producto


def codigos(pedido, por_nombre):
    out = set()
    for it in pedido.get("items", []):
        if isinstance(it, dict):
            e = it.get("ean") or it.get("codigo")
            if not e and it.get("nombre"):
                e = por_nombre.get(str(it["nombre"]).strip().lower())
        else:
            e = str(it)
        if e:
            out.add(str(e))
    return out


def main():
    pedidos = json.loads(Path(sys.argv[1]).read_text())
    d = json.loads((RAIZ / "productos.json").read_text())
    existe = {p[0] for p in d["p"]}
    por_nombre = {p[1].lower(): p[0] for p in d["p"]}

    canastas = [c & existe for c in (codigos(p, por_nombre) for p in pedidos
                                     if not p.get("prueba") and p.get("estado") != "cancelado")]
    canastas = [c for c in canastas if len(c) > 1]
    n = len(canastas)
    solo, juntos = Counter(), Counter()
    for c in canastas:
        solo.update(c)
        juntos.update(combinations(sorted(c), 2))

    cand = {}
    for (a, b), k in juntos.items():
        if k < MIN_JUNTOS:
            continue
        lift = k * n / (solo[a] * solo[b])
        if lift < MIN_LIFT:
            continue
        cand.setdefault(a, []).append((k, lift, b))
        cand.setdefault(b, []).append((k, lift, a))
    aprendido = {e: [x[2] for x in sorted(l, reverse=True)[:MAX]] for e, l in cand.items()}

    salida = RAIZ / "sugerencias.json"
    sug = json.loads(salida.read_text()) if salida.exists() else {"r": {}, "x": []}
    sug["a"] = aprendido
    salida.write_text(json.dumps(sug, ensure_ascii=False, separators=(",", ":")))
    print(f"{n} pedidos útiles, {len(aprendido)} productos con sugerencias aprendidas")


if __name__ == "__main__":
    main()
