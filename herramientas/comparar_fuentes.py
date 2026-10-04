import json, io
from PIL import Image, ImageDraw
from bajar_fotos import bajar, cuadrada
filas = json.load(open("herramientas/comparar.json"))
T = 160
hoja = Image.new("RGB", (9 * T, len(filas) * T), "white")
d = ImageDraw.Draw(hoja)
for i, fila in enumerate(filas):
    col = 0
    for nombre, urls in fila[1:]:
        for k in range(3):
            if k < len(urls):
                b = bajar(urls[k])
                if b:
                    hoja.paste(Image.open(io.BytesIO(cuadrada(b))).resize((T - 6, T - 6)), (col * T + 3, i * T + 3))
            d.text((col * T + 4, i * T + 2), f"{nombre} {k+1}", fill="red")
            col += 1
hoja.save("herramientas/comparacion.jpg", quality=80)
