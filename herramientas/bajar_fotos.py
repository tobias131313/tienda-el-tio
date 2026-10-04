"""Baja las fotos de herramientas/fotos_urls.json a fotos/<EAN>.jpg y actualiza la lista "f" de productos.json.

Corre en GitHub Actions (workflow "Bajar fotos"). Solo baja las que faltan: una foto que ya
está en fotos/ (por ejemplo, una sacada en el local) nunca se pisa.
Formato de fotos_urls.json: {"<EAN>": {"url": "...", "src": "carrefour|jumbo|dia"}}.
"""
import io, json, os, re, sys, time, urllib.request
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

def cuadrada(datos):
    im = Image.open(io.BytesIO(datos))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        fondo = Image.new("RGBA", im.size, (255, 255, 255, 255))
        fondo.alpha_composite(im)
        im = fondo
    im = im.convert("RGB")
    util = int(LADO * 0.94)
    im.thumbnail((util, util), Image.LANCZOS)
    lienzo = Image.new("RGB", (LADO, LADO), (255, 255, 255))
    lienzo.paste(im, ((LADO - im.width) // 2, (LADO - im.height) // 2))
    out = io.BytesIO()
    lienzo.save(out, "JPEG", quality=78, optimize=True, progressive=True)
    return out.getvalue()

def una(item):
    ean, url = item
    datos = bajar(url)
    if not datos:
        return ean, False
    try:
        with open(os.path.join("fotos", ean + ".jpg"), "wb") as f:
            f.write(cuadrada(datos))
        return ean, True
    except Exception:
        return ean, False

def main():
    urls = json.load(open("herramientas/fotos_urls.json", encoding="utf-8"))
    faltan = [(e, v["url"]) for e, v in urls.items() if not os.path.exists(os.path.join("fotos", e + ".jpg"))]
    print(f"{len(urls)} con link, {len(faltan)} por bajar")
    malas = []
    with ThreadPoolExecutor(8) as ex:
        for ean, ok in ex.map(una, faltan):
            if not ok:
                malas.append(ean)
    print(f"bajadas {len(faltan) - len(malas)}, fallaron {len(malas)}: {' '.join(malas[:50])}")

    datos = json.load(open("productos.json", encoding="utf-8"))
    hay = {n[:-4] for n in os.listdir("fotos") if n.endswith(".jpg")}
    datos["f"] = sorted(p[0] for p in datos["p"] if p[0] in hay)
    with open("productos.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, separators=(",", ":"))
    print(f"productos con foto propia: {len(datos['f'])} de {len(datos['p'])}")

if __name__ == "__main__":
    main()
