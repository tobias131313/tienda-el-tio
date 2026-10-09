"""Arma extras.json para la tienda: marca de cada producto y los más vendidos (para ordenar la búsqueda).

Uso: python herramientas/armar_extras.py maestro_productos.csv productos.json [ventas_por_producto.js] > extras.json

- Marca: primera palabra del nombre de SAG (dos si empieza con La, El, Don, Dos...), si se repite en al menos
  3 productos y no es una palabra genérica (Aceite, Yerba...). Se muestra como aparece en el nombre de la tienda.
- Más vendidos: solo el orden de los códigos (sin cantidades ni plata), sacado de las ventas de Vendita.
El nightly de precios no toca este archivo.
"""
import collections, csv, json, re, sys, unicodedata

STOP = {'LA','EL','LOS','LAS','DON','DOÑA','SAN','SANTA','DE','DEL','MR','DR','VIA','VILLA','TIO','LE','CASA','DOS','TRES','GRAN','SUPER','MI','LO','BON'}
GEN = set("""ACEITE ARROZ AZUCAR FIDEOS YERBA LECHE QUESO JABON SHAMPOO GALLETITAS GALL GALLET VINO CERVEZA AGUA GASEOSA JUGO PAN HARINA
SAL CAFE TE MATE DULCE MERMELADA CREMA YOGUR MANTECA PAPEL DETERGENTE LAVANDINA ESPONJA BOLSA VELA ALFAJOR CHOCOLATE CARAMELOS CHICLE
PILAS LAMPARA PEINE CEPILLO PASTA DESODORANTE TOALLITAS PAÑALES ALIMENTO GALLETA PURE SALSA TOMATE ARVEJAS CHOCLO ATUN LENTEJAS POROTOS
POLENTA AVENA CEREAL TAPA TAPAS PREPIZZA HUEVO HUEVOS SALAME JAMON MORTADELA BONDIOLA SALCHICHA HAMBURGUESA MILANESA POLLO CARNE PECETO
NALGA VACIO ASADO CHORIZO MORCILLA FIDEO VASO VASOS PLATO PLATOS CUCHARA TENEDOR CUCHILLO OLLA SARTEN BALDE ESCOBA SECADOR TRAPO REJILLA
GUANTE GUANTES INSECTICIDA SUAVIZANTE LIMPIADOR APERITIVO FERNET WHISKY VODKA GIN RON LICOR SIDRA CHAMPAGNE ESPUMANTE HELADO PAPAS PALITOS
MANI CHIZITOS TURRON OBLEA BUDIN BIZCOCHUELO MAGDALENAS TOSTADAS GRISINES PANCITOS FACTURA FACTURAS BANANA MANZANA NARANJA LIMON PAPA
CEBOLLA ZANAHORIA ACEITUNAS PICKLES MAYONESA KETCHUP MOSTAZA VINAGRE CALDO SOPA EDULCORANTE GELATINA FLAN POSTRE BOLSAS ROLLO SERVILLETAS
PAÑUELOS ALGODON HISOPOS MAQUINA AFEITADORA PRESERVATIVOS PROTECTORES TAMPONES CREMAS ACONDICIONADOR TINTURA COLONIA PERFUME TALCO
ESMALTE ENCENDEDOR FOSFOROS CARBON HIELO SODA BARRA QUESITO TARTA EMPANADAS RAVIOLES ÑOQUIS SORRENTINOS CANELONES LASAGNA PIZZA BIFE
COSTILLA MATAMBRE PALETA CUADRADA OSOBUCO PICADA CHURRASCO SUPREMA PATA ALAS FILET MERLUZA CAJA PACK X""".split())

def norm(s):
    return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().upper()

def cand(s):
    w = re.sub(r"[^A-ZÑ0-9 &']", ' ', s.upper()).split()
    if not w or w[0].isdigit():
        return None
    return w[0] + ' ' + w[1] if (w[0] in STOP or len(w[0]) <= 2) and len(w) > 1 else w[0]

def display(c, tienda):
    # Busca en el nombre de la tienda las palabras que empiezan como la marca de SAG ("LA SERE" -> "La Serenísima").
    cw = norm(c).split()
    tw = tienda.split()
    for i in range(len(tw) - len(cw) + 1):
        if all(norm(tw[i + k]).strip('.,()-').startswith(cw[k]) for k in range(len(cw))):
            return ' '.join(tw[i:i + len(cw)]).strip('.,()-')
    return None

def main(maestro, productos, ventas=None):
    eans = {p[0] for p in json.load(open(productos, encoding='utf-8'))['p']}
    rows = [r for r in csv.DictReader(open(maestro, encoding='utf-8')) if r['ean'] in eans]
    per = {r['ean']: cand(r['nombre_sag']) for r in rows}
    cnt = collections.Counter(per.values())
    ok = {c for c, n in cnt.items() if c and n >= 3 and c.split()[-1] not in GEN and c not in GEN}
    shows = collections.defaultdict(collections.Counter)
    for r in rows:
        c = per[r['ean']]
        if c in ok:
            shows[c][display(c, r['nombre_tienda']) or c.title()] += 1
    names = sorted({shows[c].most_common(1)[0][0] for c in ok}, key=lambda s: norm(s))
    idx = {n: i for i, n in enumerate(names)}
    m = {e: idx[shows[c].most_common(1)[0][0]] for e, c in per.items() if c in ok}
    top = []
    if ventas:
        txt = open(ventas, encoding='utf-8').read()
        data = json.loads(txt[txt.index('{'):txt.rindex('}') + 1])
        tot = [(sum(p[4]), p[0]) for p in data['p'] if p[0] in eans]
        top = [e for n, e in sorted(tot, reverse=True) if n > 0]
    json.dump({'b': names, 'm': m, 'top': top}, sys.stdout, ensure_ascii=False, separators=(',', ':'))

if __name__ == '__main__':
    main(*sys.argv[1:])
