# Buzón de carteles (caja 4)

El programa de la caja 4 (`carteles/caja/carteles.ps1`) revisa esta carpeta cada 2 minutos y manda a imprimir
cada PDF nuevo en la Brother. Lo que ya imprimió queda anotado en `C:\carteles\buzon.txt`, así no se repite.

- Nombre: `AAAA-MM-DD_descripcion__EAN1_EAN2.pdf`. Los EAN del final no llevan cartel blanco ese día
  (para que no salgan los dos carteles cuando una oferta cambia el precio en Vendita).
- Subir primero el PDF y después cambiar el precio en Vendita.
- Hoja A4, al 100 %. Las ofertas se imprimen en hoja amarilla.
- La carpeta es pública: solo carteles con precio de góndola, nunca costos.
