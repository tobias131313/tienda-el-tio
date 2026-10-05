"""Arma sugerencias.json: qué productos mostrar en "Va bien con" (venta cruzada).

Dos fuentes, en este orden de prioridad en la tienda:
  "a" (aprendido): pares que se compran juntos en pedidos reales. Lo escribe aprender_sugerencias.py.
  "x" y "r" (reglas a mano): por tipo de producto. Las arma este script con REGLAS.

Uso:
  python3 herramientas/armar_sugerencias.py [EstadisticasVenta.xlsx]

El Excel de ventas de Vendita es opcional: sirve para elegir los productos más vendidos de cada tipo.
No se sube al repo (trae costos). Sin él se eligen los que tienen foto.
Conserva lo aprendido ("a") que ya hubiera en sugerencias.json.
"""
import json, re, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
POR_TIPO = 2      # productos por cada sugerencia
MAX = 8           # sugerencias por producto

# Sugerencias reutilizables: (subcategorías donde buscar, palabra en el nombre o None, palabra a excluir o None)
T = {
    "pan_hamb": (["Panes y facturas", "Pan lactal y de molde"], r"hambur", None),
    "pan_pancho": (["Panes y facturas", "Pan lactal y de molde"], r"pancho", None),
    "cheddar": (["Quesos de fiambrería", "Quesos", "Quesos untables"], r"cheddar", r"dip"),
    "ketchup": (["Aderezos y salsas"], r"ketchup", None),
    "mayonesa": (["Aderezos y salsas"], r"mayonesa", None),
    "mostaza": (["Aderezos y salsas"], r"mostaza", None),
    "papas_cong": (["Vegetales y papas congeladas"], r"papa", None),
    "papas_pay": (["Papas fritas y snacks"], r"pay|paille", None),
    "papas": (["Papas fritas y snacks"], r"papa", None),
    "palitos": (["Palitos, chizitos y maníes"], None, None),
    "gaseosa": (["Gaseosas"], None, None),
    "coca": (["Gaseosas"], r"coca", r"zero|light"),
    "cerveza": (["Cervezas"], None, None),
    "vino": (["Vinos tintos"], None, None),
    "carbon": (["Velas, fósforos y encendedores"], r"carb[oó]n", None),
    "chimi": (["Especias y condimentos", "Aderezos y salsas"], r"chimichurri", None),
    "sal_gruesa": (["Sal"], r"gruesa|parrill", None),
    "salsa": (["Puré y salsas de tomate"], None, None),
    "rallado": (["Quesos", "Quesos de fiambrería"], r"rallad", None),
    "crema": (["Crema de leche"], None, None),
    "aceite": (["Aceites y vinagres"], r"aceite", None),
    "caldo": (["Caldos y sopas"], None, None),
    "muzza": (["Quesos de fiambrería", "Quesos"], r"muzza|mozza", None),
    "aceitunas": (["Aceitunas y encurtidos"], r"aceituna", None),
    "oregano": (["Especias y condimentos"], r"or[eé]gano", None),
    "huevos": (["Huevos"], None, None),
    "pan_rallado": (["Pan rallado y rebozadores"], None, None),
    "pure": (["Purés de papas"], None, None),
    "arroz": (["Arroz"], None, None),
    "azucar": (["Azúcar y endulzantes"], r"az[uú]car", None),
    "galle_dulce": (["Galletitas dulces"], None, None),
    "bizcochos": (["Obleas y bizcochos"], r"bizcoch", None),
    "leche": (["Leches"], None, None),
    "cafe": (["Café, té y mate cocido"], None, None),
    "cereales": (["Cereales y avenas"], None, None),
    "ddl": (["Dulce de leche"], None, None),
    "mermelada": (["Dulces y mermeladas"], None, None),
    "manteca": (["Manteca y margarina"], None, None),
    "pan_lactal": (["Pan lactal y de molde"], None, r"hambur|pancho"),
    "jamon": (["Jamones y paletas"], None, None),
    "queso_fiam": (["Quesos de fiambrería"], None, r"rallad"),
    "salame": (["Salames y embutidos"], None, None),
    "untable": (["Quesos untables"], None, None),
    "esponja": (["Esponjas, trapos y paños"], None, None),
    "rollo": (["Rollos de cocina y servilletas"], None, None),
    "suavizante": (["Suavizantes"], None, None),
    "lavandina": (["Lavandinas"], None, None),
    "jabon_tocador": (["Jabones de tocador"], None, None),
    "toallitas_bebe": (["Higiene y accesorios de bebé"], r"toallit", None),
    "harina": (["Harinas y premezclas"], r"harina", None),
    "repost": (["Postres y repostería"], None, None),
    "yogur": (["Yogures"], None, None),
}

# Por subcategoría (de productos.json) -> sugerencias, en orden
REGLAS = {
    "Hamburguesas y medallones": ["pan_hamb", "cheddar", "ketchup", "mayonesa", "papas_cong", "gaseosa"],
    "Carne vacuna": ["carbon", "chimi", "sal_gruesa", "vino", "gaseosa"],
    "Achuras y embutidos frescos": ["carbon", "chimi", "vino", "gaseosa"],
    "Cerdo": ["carbon", "chimi", "sal_gruesa", "vino"],
    "Pollo": ["papas_cong", "pure", "arroz", "aceite", "gaseosa"],
    "Milanesas y preparados": ["papas_cong", "pure", "mayonesa", "gaseosa"],
    "Rebozados y nuggets": ["papas_cong", "ketchup", "mayonesa", "gaseosa"],
    "Fideos secos": ["salsa", "rallado", "aceite", "crema"],
    "Pastas frescas": ["salsa", "rallado", "crema"],
    "Ñoquis y ravioles": ["salsa", "rallado", "crema"],
    "Arroz": ["salsa", "caldo", "rallado", "aceite"],
    "Puré y salsas de tomate": ["rallado", "aceite", "oregano"],
    "Prepizzas y tapas": ["muzza", "salsa", "aceitunas", "oregano"],
    "Tapas de empanadas y tartas": ["huevos", "queso_fiam", "jamon", "aceitunas"],
    "Yerba mate": ["azucar", "galle_dulce", "bizcochos"],
    "Café, té y mate cocido": ["leche", "azucar", "galle_dulce", "pan_lactal"],
    "Leches": ["cafe", "cereales", "galle_dulce", "ddl"],
    "Cereales y avenas": ["leche", "yogur"],
    "Pan lactal y de molde": ["jamon", "queso_fiam", "manteca", "ddl", "mermelada"],
    "Panes y facturas": ["jamon", "queso_fiam", "manteca", "ddl"],
    "Jamones y paletas": ["pan_lactal", "queso_fiam", "manteca"],
    "Quesos de fiambrería": ["pan_lactal", "jamon", "salame"],
    "Salames y embutidos": ["queso_fiam", "vino", "cerveza"],
    "Gaseosas": ["papas", "palitos"],
    "Cervezas": ["papas", "palitos", "salame"],
    "Fernet y aperitivos": ["coca"],
    "Vodka, gin y ron": ["gaseosa"],
    "Whisky": ["gaseosa"],
    "Vinos tintos": ["queso_fiam", "salame", "carbon"],
    "Papas fritas y snacks": ["gaseosa", "cerveza", "palitos"],
    "Palitos, chizitos y maníes": ["gaseosa", "cerveza", "papas"],
    "Detergentes y lavavajillas": ["esponja", "rollo"],
    "Jabón para ropa": ["suavizante", "lavandina"],
    "Papel higiénico": ["rollo", "jabon_tocador"],
    "Pañales de bebé": ["toallitas_bebe"],
    "Harinas y premezclas": ["huevos", "azucar", "manteca", "repost"],
    "Huevos": ["harina", "aceite", "pan_rallado"],
    "Dulce de leche": ["galle_dulce", "pan_lactal"],
}

# Por palabra en el nombre (gana sobre la subcategoría): regex -> sugerencias
ESPECIALES = [
    (r"salchich", ["pan_pancho", "mostaza", "ketchup", "papas_pay", "gaseosa"]),
    (r"picada|carne molida", ["tapas_emp", "huevos", "salsa", "pure"]),
    (r"nalga|cuadrada|bola de lomo|peceto", ["pan_rallado", "huevos", "papas_cong", "pure"]),
    (r"choriz|morcilla", ["chimi", "carbon"]),
]
T["tapas_emp"] = (["Tapas de empanadas y tartas"], None, None)


def ventas_por_ean(xlsx):
    import openpyxl
    ws = openpyxl.load_workbook(xlsx, read_only=True).active
    out = {}
    for r in list(ws.iter_rows(values_only=True))[1:]:
        if r[0] and isinstance(r[4], (int, float)):
            out[str(r[0]).strip()] = out.get(str(r[0]).strip(), 0) + r[4]
    return out


def main():
    d = json.loads((RAIZ / "productos.json").read_text())
    S, P, fotos = d["s"], d["p"], set(d.get("f", []))
    vendidos = ventas_por_ean(sys.argv[1]) if len(sys.argv) > 1 else {}
    sub = lambda p: S[p[5]] if isinstance(p[5], int) and 0 <= p[5] < len(S) else ""
    # Más vendido primero, después con foto, después nombre corto
    rank = sorted(P, key=lambda p: (-vendidos.get(p[0], 0), p[0] not in fotos, len(p[1])))

    elegidos = {}
    for k, (subs, si, no) in T.items():
        r = [p[0] for p in rank
             if (subs is None or sub(p) in subs)
             and (si is None or re.search(si, p[1], re.I))
             and not (no and re.search(no, p[1], re.I))
             and (p[0] in fotos or vendidos.get(p[0]))]
        sin_rep, vistos = [], set()
        for e in r:
            n = next(p[1].lower() for p in P if p[0] == e)
            if n not in vistos:
                sin_rep.append(e); vistos.add(n)
            if len(sin_rep) == POR_TIPO:
                break
        elegidos[k] = sin_rep
        if not r:
            print("sin productos para", k)

    nombre = {p[0]: p[1].lower() for p in P}

    def lista(ks):
        # Una de cada tipo primero y después la segunda; sin nombres repetidos
        out, vistos = [], set()
        for ronda in range(POR_TIPO):
            for k in ks:
                if ronda < len(elegidos[k]):
                    e = elegidos[k][ronda]
                    if nombre[e] not in vistos:
                        out.append(e); vistos.add(nombre[e])
        return out[:MAX]

    faltan = [s for s in REGLAS if s not in S]
    if faltan:
        print("subcategorías que no existen:", faltan)
    salida = RAIZ / "sugerencias.json"
    viejo = json.loads(salida.read_text()) if salida.exists() else {}
    res = {
        "r": {s: lista(ks) for s, ks in REGLAS.items()},
        "x": [[rx, lista(ks)] for rx, ks in ESPECIALES],
        "a": viejo.get("a", {}),
    }
    salida.write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")))
    print("ok:", len(res["r"]), "tipos,", len(res["x"]), "especiales,", len(res["a"]), "aprendidos")


if __name__ == "__main__":
    main()
