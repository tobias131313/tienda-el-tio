# Súper El Tío a Domicilio

Tienda de pedidos online del Súper El Tío (Moreno). El cliente arma el carrito y el pedido se envía por WhatsApp al 11 2865-6389.

- `index.html`: la página (catálogo, carrito, datos de entrega y armado del mensaje de WhatsApp).
- `productos.json`: productos y precios. Formato `{"r": [rubros], "p": [[EAN, nombre, índice de rubro, precio final con IVA]]}`.

Reglas del pedido (en `index.html`): mínimo $25.000, envío $2.000, envío gratis desde $50.000.

Para actualizar precios se regenera `productos.json` desde la última lista de precios del súper.
