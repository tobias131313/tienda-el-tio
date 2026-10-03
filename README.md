# Súper El Tío a Domicilio

Tienda de pedidos online del Súper El Tío (Moreno). El cliente arma el carrito y el pedido se envía por WhatsApp al 11 2865-6389.

- `index.html`: la página (catálogo, carrito, datos de entrega y armado del mensaje de WhatsApp).
- `productos.json`: productos y precios. Formato `{"r": [rubros], "p": [[EAN, nombre, índice de rubro, precio final con IVA]]}`.

Reglas del pedido (en `index.html`): mínimo $25.000, envío $2.000, envío gratis desde $50.000.

Para actualizar precios se regenera `productos.json` desde la última lista de precios del súper.

## Fotos

1. Fotos propias: archivo `fotos/<EAN>.jpg` y el EAN agregado a la lista `"f"` de `productos.json`. Tienen prioridad.
2. Si no hay foto propia, la página busca la foto por código de barras en Open Food Facts (base libre).
3. Si no hay ninguna, se muestra la inicial del producto.

`fotos.html` es la herramienta del personal: busca o escanea el producto, saca la foto, la deja cuadrada en 800 px y la guarda como `<EAN>.jpg`. Las fotos se suben a la carpeta `fotos/` desde GitHub y la tienda las detecta sola.
