# Súper El Tío a Domicilio

Tienda de pedidos online del Súper El Tío (Moreno). El cliente arma el carrito y el pedido se envía por WhatsApp al 11 2865-6389.

- `index.html`: la tienda con la marca del local (diseño A: franja azul, precios amarillos, `logo.jpg`). Respaldos: `verde.html` (versión verde anterior) y `anterior.html` (versión de lista). `diseno-a/b/c.html` son las opciones de diseño que se mostraron.
- Link de prueba para amigos: agregar `?prueba` a la dirección; el pedido de WhatsApp llega marcado como PEDIDO DE PRUEBA.
- `productos.json`: productos y precios. Formato `{"r": [rubros], "p": [[EAN, nombre, índice de rubro, precio final con IVA]]}`.

Reglas del pedido (en `index.html`): mínimo $25.000, envío $2.000, envío gratis desde $50.000.

Para actualizar precios se regenera `productos.json` desde la última lista de precios del súper.

## Fotos

1. Fotos guardadas: archivo `fotos/<EAN>.jpg` y el EAN agregado a la lista `"f"` de `productos.json`. Tienen prioridad.
   La mayoría salen de las tiendas online de Carrefour, Jumbo y Día buscando por código de barras. Los links quedan en `herramientas/fotos_urls.json` y el workflow "Bajar fotos" (`herramientas/bajar_fotos.py`) las baja cuando ese archivo cambia: cuadradas de 400 px, fondo blanco, sin la franja de color de e-commerce y salteando los carteles de "imagen no disponible". Nunca pisa una foto que ya está.
2. Si no hay foto propia, la página busca la foto por código de barras en Open Food Facts (base libre).
3. Si no hay ninguna, se muestra la inicial del producto.

`fotos.html` es la herramienta del personal: busca o escanea el producto, saca la foto, la deja cuadrada en 800 px y la guarda como `<EAN>.jpg`. Las fotos se suben a la carpeta `fotos/` desde GitHub y la tienda las detecta sola.

## Nombres y precios

`herramientas/armar_productos.py` arma `productos.json` cruzando por EAN la lista de precios del súper (privada, no va en este repositorio) con la lista maestra de nombres y subcategorías. El precio siempre sale de la lista de precios; el nombre de la tienda, de la lista maestra. Un EAN nuevo sale con el nombre de SAG hasta que se le asigne uno.
