# Carteles automáticos en la caja 4

Se instala desde PowerShell (administrador) con el comando del hilo. El instalador:
1. Copia todo a `C:\carteles`, con permiso para todos los usuarios.
2. Baja SumatraPDF.
3. Busca la Brother. La de tickets y la predeterminada no se tocan.
4. Pide el usuario de Vendita y lo guarda cifrado para la PC.
5. Guarda los precios de hoy, sin imprimir nada.
6. Crea la tarea "Carteles El Tío", que arranca al iniciar sesión con cualquier usuario (cajero o administrador).

Si hay dos sesiones abiertas, corre una sola copia.

## Cómo funciona
`carteles.ps1` hace dos cosas:
- Cada 15 minutos, de 7 a 22 h, lee Vendita (solo lectura) y arma el PDF de los productos que cambiaron de precio.
- Cada 30 segundos imprime lo que haya en `C:\carteles\pendientes`.

El registro queda en `C:\carteles\registro.txt`.

## Desinstalar
1. Borrar la tarea "Carteles El Tío" en el Programador de tareas.
2. Borrar `C:\carteles`.
