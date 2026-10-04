"""Baja las fotos de herramientas/fotos_urls.json a fotos/<EAN>.jpg y actualiza la lista "f" de productos.json.

Corre en GitHub Actions (workflow "Bajar fotos"). Solo baja las que faltan: una foto que ya
está en fotos/ (por ejemplo, una sacada en el local) nunca se pisa.
Formato de fotos_urls.json: {"<EAN>": [["carrefour|jumbo|dia", "url"], ...]} en orden de preferencia.
Si una tienda devuelve el cartel de "imagen no disponible", se prueba la siguiente; esos carteles
quedan anotados en herramientas/fotos_vacias.txt. También se recorta la franja de color con nombre y tamaño.
"""
import hashlib, io, json, os, re, time, urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

LADO = 400

def bajar(url):
    # VTEX entrega la imagen ya achicada si se le pide /ids/<id>-ancho-alto/
    url = re.sub(r"/ids/(\d+)/", r"/ids/\1-%d-%d/" % (LADO, LADO), url, count=1)
    for intento in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r:
                return r.read()
        except Exception:
            time.sleep(2 * (intento + 1))
    return None

def sin_bordes(im):
    """Recorta el margen blanco alrededor del producto."""
    caja = im.convert("L").point(lambda v: 255 if v < 235 else 0).getbbox()
    return im.crop(caja) if caja else im

def quitar_franja(im):
    """Recorta la franja de color con nombre y tamaño que traen a la derecha muchas fotos de e-commerce."""
    g = im.convert("L"); w, h = g.size; px = g.load()
    filas = range(0, h, max(1, h // 200))
    col = [sum(1 for y in filas if px[x, y] < 235) / len(filas) for x in range(w)]
    x = w - 1
    while x > w * 0.8 and col[x] < 0.4:
        x -= 1
    if col[x] < 0.4:
        return im
    fin = x
    while x > 0 and col[x] >= 0.4:
        x -= 1
    if not (h * 0.06 <= fin - x <= min(h * 0.3, w * 0.45)):
        return im
    hueco = x
    while x > 0 and col[x] < 0.25:
        x -= 1
    if hueco - x < w * 0.015 or x < w * 0.3:
        return im
    return im.crop((0, 0, x + max(2, w // 100), h))

def cuadrada(datos):
    im = Image.open(io.BytesIO(datos))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        fondo = Image.new("RGBA", im.size, (255, 255, 255, 255))
        fondo.alpha_composite(im)
        im = fondo
    im = sin_bordes(quitar_franja(sin_bordes(im.convert("RGB"))))
    # La misma franja a veces viene abajo (nombre del sabor, "x6", "Rinde 1 L"): se gira la foto y se usa la misma regla.
    im = sin_bordes(quitar_franja(im.rotate(90, expand=True)).rotate(-90, expand=True))
    util = int(LADO * 0.94)
    im.thumbnail((util, util), Image.LANCZOS)
    lienzo = Image.new("RGB", (LADO, LADO), (255, 255, 255))
    lienzo.paste(im, ((LADO - im.width) // 2, (LADO - im.height) // 2))
    out = io.BytesIO()
    lienzo.save(out, "JPEG", quality=78, optimize=True, progressive=True)
    return out.getvalue()

def md5(b):
    return hashlib.md5(b).hexdigest()

def main():
    urls = json.load(open("herramientas/fotos_urls.json", encoding="utf-8"))
    ruta_vacias = "herramientas/fotos_vacias.txt"
    vacias = set(open(ruta_vacias).read().split()) if os.path.exists(ruta_vacias) else set()
    # Borra fotos que resultaron ser carteles de "imagen no disponible".
    for n in os.listdir("fotos"):
        if n.endswith(".jpg") and md5(open(os.path.join("fotos", n), "rb").read()) in vacias:
            os.remove(os.path.join("fotos", n))

    def probar(item):
        ean, candidatas = item
        for _, url in candidatas:
            datos = bajar(url)
            if not datos:
                continue
            try:
                jpg = cuadrada(datos)
            except Exception:
                continue
            if md5(jpg) not in vacias:
                return ean, jpg
        return ean, None

    faltan = {e: c for e, c in urls.items() if not os.path.exists(os.path.join("fotos", e + ".jpg"))}
    print(f"{len(urls)} con link, {len(faltan)} por bajar")
    while faltan:
        bajadas = {}
        with ThreadPoolExecutor(8) as ex:
            for ean, jpg in ex.map(probar, faltan.items()):
                if jpg:
                    bajadas[ean] = jpg
        # La misma imagen en 3 o más productos distintos es un cartel de "sin imagen": se descarta y se prueba otra tienda.
        repetidas = Counter(md5(j) for j in bajadas.values())
        nuevas = {h for h, n in repetidas.items() if n >= 3}
        for ean, jpg in bajadas.items():
            if md5(jpg) not in nuevas:
                with open(os.path.join("fotos", ean + ".jpg"), "wb") as f:
                    f.write(jpg)
        print(f"bajadas {len(bajadas)}, carteles nuevos de sin imagen: {len(nuevas)}")
        if not nuevas:
            break
        vacias |= nuevas
        faltan = {e: c for e, c in faltan.items() if e in bajadas and md5(bajadas[e]) in nuevas}
    with open(ruta_vacias, "w") as f:
        f.write("\n".join(sorted(vacias)) + "\n")

    datos = json.load(open("productos.json", encoding="utf-8"))
    hay = {n[:-4] for n in os.listdir("fotos") if n.endswith(".jpg")}
    datos["f"] = sorted(p[0] for p in datos["p"] if p[0] in hay)
    with open("productos.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, separators=(",", ":"))
    print(f"productos con foto: {len(datos['f'])} de {len(datos['p'])}")

if __name__ == "__main__":
    main()
