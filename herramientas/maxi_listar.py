"""Lista los productos de Maxiconsumo (nombre y foto) recorriendo sus categorías. Corre en GitHub Actions."""
import json, re, sys, time, urllib.request, urllib.parse
B = "https://www.maxiconsumo.com/sucursal_moreno/"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
ITEM = re.compile(r'<img class="product-image-photo" src="([^"]+)"[^>]*alt="([^"]*)"')
out = {}
for cat in sys.argv[1:]:
    for p in range(1, 80):
        url = B + cat + ".html?" + urllib.parse.urlencode({"product_list_limit": 96, "p": p})
        try:
            html = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode("utf-8", "ignore")
        except Exception as e:
            print(cat, p, e); break
        nuevos = 0
        for src, alt in ITEM.findall(html):
            src = re.sub(r"/cache/[0-9a-f]+/", "/", src)
            if src not in out:
                out[src] = {"nombre": alt, "cat": cat}; nuevos += 1
        print(cat, p, nuevos, flush=True)
        if not nuevos: break
        time.sleep(0.5)
json.dump([dict(img=k, **v) for k, v in out.items()], open("herramientas/maxi_productos.json", "w"), ensure_ascii=False, indent=0)
