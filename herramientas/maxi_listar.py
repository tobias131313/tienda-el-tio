"""Lista productos de Maxiconsumo (nombre, link, foto) para las marcas pedidas. Corre en GitHub Actions."""
import json, re, sys, time, urllib.request, urllib.parse
B = "https://www.maxiconsumo.com/sucursal_moreno/catalogsearch/result/?"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
ITEM = re.compile(r'<img class="product-image-photo" src="([^"]+)"[^>]*alt="([^"]*)"')
out = {}
for marca in sys.argv[1:]:
    for p in range(1, 40):
        url = B + urllib.parse.urlencode({"q": marca, "p": p})
        try:
            html = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode("utf-8", "ignore")
        except Exception as e:
            print(marca, p, e); break
        nuevos = 0
        for src, alt in ITEM.findall(html):
            src = re.sub(r"/cache/[0-9a-f]+/", "/", src)
            if src not in out:
                out[src] = {"nombre": alt, "marca": marca}; nuevos += 1
        print(marca, p, nuevos, flush=True)
        if not nuevos: break
        time.sleep(1)
json.dump([dict(img=k, **v) for k, v in out.items()], open("herramientas/maxi_productos.json", "w"), ensure_ascii=False, indent=0)
