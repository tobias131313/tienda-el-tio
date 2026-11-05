# Carteles automáticos

1. `generar_carteles.ps1` lee Vendita (solo lectura, usuario de Claude) cada 15 minutos.
2. Compara contra `C:\carteles\precios.json`.
3. Con los productos que cambiaron de precio arma un PDF con los carteles tipo 1 (24 por hoja). Usa `plantilla.html`, abierta con Edge sin ventana.
4. Deja el PDF en `OneDrive\Carteles\pendientes`.
5. Ahí lo toma `imprimir_carteles.ps1`, que lo imprime en la Brother.

## Instalar en la PC de la caja
1. Copiá esta carpeta a `C:\carteles\auto`: plantilla.html, JsBarcode.all.min.js y fonts.
2. Copiá `generar_carteles.ps1` a `C:\carteles\`.
3. Corré una vez a mano:

   `powershell -ExecutionPolicy Bypass -File C:\carteles\generar_carteles.ps1 -SoloBase`

   Pide el usuario de Vendita y lo tipea Tobias. Guarda la base de precios y no imprime nada.
4. En el loop de `imprimir_carteles.ps1`, llamarlo cada 15 minutos entre las 7 y las 22.

## Reglas
- No se hacen carteles de:
  - productos discontinuados;
  - productos borrados;
  - productos con precio de $10 o menos (los genéricos).
- Si de golpe cambian más de 300 productos, el PDF va a `C:\carteles\revisar` y no se imprime solo.
- La marca sale de la primera palabra del nombre, salvo las marcas de dos palabras conocidas.
- En verdulería, carnicería, fiambrería y panadería la marca va vacía: eso está pendiente de decidir.
