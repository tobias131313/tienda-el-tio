# Carteles automáticos en la caja 4

Se instala desde PowerShell (administrador) con el comando del hilo. El instalador:
1. Copia todo a `C:\carteles`, con permiso para todos los usuarios.
2. Baja SumatraPDF.
3. Busca la Brother. La de tickets y la predeterminada no se tocan.
4. Pide el usuario de Vendita y lo guarda cifrado para la PC.
5. Guarda los precios de hoy, sin imprimir nada.
6. Pide la clave de Windows del administrador y crea la tarea "Carteles El Tío", que corre con ese usuario al prender la PC, sin importar quién use la caja después. Como "sistema" no funciona: Edge no arma el PDF.


## Cómo funciona
`carteles.ps1` hace dos cosas:
- Cada 15 minutos, de 7 a 22 h, lee Vendita (solo lectura) y arma el PDF de los productos que cambiaron de precio.
- Cada 30 segundos imprime lo que haya en `C:\carteles\pendientes`.

El registro queda en `C:\carteles\registro.txt`.

## Desinstalar
1. Borrar la tarea "Carteles El Tío" en el Programador de tareas.
2. Borrar `C:\carteles`.

## Instalado el 05/11/2026 en la caja 4 (PC Usuario_11, Windows 11)
- Brother DCP-1617NW por USB (Windows la llama "Brother DCP-1610NW series"). La de tickets (POS80) no se toca.
- Lo que falló y cómo se resolvió:
  - El antivirus marcaba `plantilla.html` como troyano cuando tenía CSS y JS adentro: por eso están separados en `carteles.css` y `carteles.js`.
  - El instalador de SumatraPDF no imprime: hay que usar el zip portable, que el instalador baja solo.
  - Como tarea del sistema, Edge no genera el PDF: la tarea corre con el usuario administrador.

## Buzón (07/11/2026)
Cada 2 minutos el programa mira la carpeta `buzon/` de la rama `carteles-buzon` de este repo y baja a
`C:\carteles\pendientes` los PDF nuevos (se imprimen solos). Detalle en `buzon/LEEME.md`.

Actualizar la caja 4 (PowerShell como administrador):
```
Stop-ScheduledTask 'Carteles El Tio'; Invoke-WebRequest 'https://raw.githubusercontent.com/tobias131313/tienda-el-tio/carteles-buzon/carteles/caja/carteles.ps1' -OutFile C:\carteles\carteles.ps1 -UseBasicParsing; Start-ScheduledTask 'Carteles El Tio'
```
