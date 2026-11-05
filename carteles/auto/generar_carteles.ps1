# Genera el PDF de carteles (tipo 1, 24 por hoja) de los productos que cambiaron de precio en Vendita.
# SOLO LECTURA de Vendita. Lo llama imprimir_carteles.ps1 cada 15 minutos (7 a 22 h).
# Primera vez: correrlo a mano (pide el usuario de Vendita y guarda la base de precios, no imprime nada).
# Archivos:
#   C:\carteles\vendita.cred      usuario/clave cifrados para este usuario de Windows (nunca en texto)
#   C:\carteles\precios.json      ultimo precio visto de cada producto
#   C:\carteles\auto\             plantilla.html + fonts + JsBarcode (diseño de los carteles)
#   OneDrive\Carteles\pendientes  donde deja el PDF (imprimir_carteles.ps1 lo imprime)
#   C:\carteles\revisar           si cambian mas de 300 productos de golpe, el PDF va aca y NO se imprime solo
param([switch]$SoloBase)
$ErrorActionPreference = 'Stop'
$dir     = 'C:\carteles'
$B       = 'https://gestion.venditaenlinea.com'
$cred    = Join-Path $dir 'vendita.cred'
$estado  = Join-Path $dir 'precios.json'
$work    = Join-Path $dir 'auto'
$od      = Join-Path $env:USERPROFILE 'OneDrive\Carteles\pendientes'
$pend    = if (Test-Path (Split-Path $od)) { $od } else { Join-Path $dir 'pendientes' }
$revisar = Join-Path $dir 'revisar'
$log     = Join-Path $dir 'registro_generar.txt'
New-Item -ItemType Directory -Force $pend, $revisar | Out-Null
function Log($m) { Add-Content $log ("{0:yyyy-MM-dd HH:mm} {1}" -f (Get-Date), $m); Write-Host $m }
function Json($url, $hdr, $body) {
  $p = @{ Uri = $url; UseBasicParsing = $true; TimeoutSec = 180 }
  if ($hdr)  { $p.Headers = $hdr }
  if ($body) { $p.Method = 'Post'; $p.Body = [Text.Encoding]::UTF8.GetBytes($body); $p.ContentType = 'application/json' }
  for ($i = 1; $i -le 4; $i++) {
    try { $r = Invoke-WebRequest @p; return ([Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray()) | ConvertFrom-Json) }
    catch { if ($i -eq 4) { throw }; Start-Sleep -Seconds ([math]::Pow(2, $i)) }
  }
}

if (-not (Test-Path $cred)) {
  $c = Get-Credential -Message 'Usuario de Vendita para los carteles (el de Claude, solo lectura)'
  if (-not $c) { throw 'Sin usuario de Vendita' }
  $c | Export-Clixml $cred
}
$c = Import-Clixml $cred
$tok = (Json "$B/api/cuentas/login" $null (@{ UserName = $c.UserName; Password = $c.GetNetworkCredential().Password; RolId = '1' } | ConvertTo-Json)).token
$h = @{ Authorization = "Bearer $tok" }

# Catalogo completo (precio de venta actual)
$prods = @{}; $last = 0
do {
  $j = Json "$B/api/productos/ChunkPorId?EmpresaID=380&lastProductoId=$last" $h
  foreach ($p in $j.productos) {
    if ($p.borrado) { continue }
    $cods = @($p.codigosBarra | Where-Object { $_.codigo } | ForEach-Object { [string]$_.codigo })
    $ean  = @($cods | Where-Object { $_.Length -ge 8 })[0]
    $prods[[string]$p.productoId] = [pscustomobject]@{
      nombre = ([string]$p.nombre).Trim(); precio = [math]::Round([double]$p.precio_venta)
      ean = [string]$ean; cod = [string]$p.codigoInterno; rubro = [string]$p.categoria.rubro; disc = [bool]$p.discontinuado }
  }
  $last = $j.ultimoProductoId
} while ($j.hayMas)
if ($prods.Count -lt 1000) { throw "Vendita devolvio pocos productos ($($prods.Count)), no toco nada" }

$nuevo = @{}; foreach ($k in $prods.Keys) { $nuevo[$k] = $prods[$k].precio }
function Guardar { $nuevo | ConvertTo-Json -Compress | Set-Content $estado -Encoding UTF8 }
if ($SoloBase -or -not (Test-Path $estado)) { Guardar; Log "Base de precios guardada ($($nuevo.Count) productos). No se imprime nada."; return }

$viejo = @{}
(Get-Content $estado -Raw | ConvertFrom-Json).PSObject.Properties | ForEach-Object { $viejo[$_.Name] = [double]$_.Value }
$cambios = @($prods.Keys | Where-Object {
    $p = $prods[$_]; (-not $p.disc) -and $p.precio -gt 10 -and ((-not $viejo.ContainsKey($_)) -or $viejo[$_] -ne $p.precio)
  } | ForEach-Object { $prods[$_] } | Sort-Object rubro, nombre)
if ($cambios.Count -eq 0) { Guardar; return }

# Arma el PDF con Edge (sin ventana) a partir de la plantilla
$lista = @($cambios | Select-Object nombre, precio, ean, cod, rubro)
$js = "var HOY='" + (Get-Date -Format 'dd/MM/yy') + "';`nvar CARTELES=" + (ConvertTo-Json -InputObject $lista -Compress) + ";"
[IO.File]::WriteAllText((Join-Path $work 'datos.js'), $js, (New-Object Text.UTF8Encoding $false))
$edge = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe", "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { throw 'No encuentro Microsoft Edge' }
$nombre = "Carteles_{0:yyyy-MM-dd_HHmm}_{1}prod.pdf" -f (Get-Date), $cambios.Count
$tmp = Join-Path $env:TEMP $nombre
$url = 'file:///' + ((Join-Path $work 'plantilla.html') -replace '\\', '/')
$a = @('--headless=new', '--disable-gpu', '--no-first-run', '--no-pdf-header-footer', '--virtual-time-budget=8000',
       "--user-data-dir=`"$env:TEMP\carteles-edge`"", "--print-to-pdf=`"$tmp`"", $url)
$pr = Start-Process $edge -ArgumentList $a -PassThru -WindowStyle Hidden
if (-not $pr.WaitForExit(120000)) { $pr.Kill(); throw 'Edge no termino el PDF' }
if (-not (Test-Path $tmp) -or (Get-Item $tmp).Length -lt 2000) { throw 'El PDF salio vacio' }

if ($cambios.Count -gt 300) { Move-Item $tmp (Join-Path $revisar $nombre) -Force; Log "$($cambios.Count) cambios: PDF en revisar (no se imprime solo)" }
else { Move-Item $tmp (Join-Path $pend $nombre) -Force; Log "$($cambios.Count) carteles a imprimir: $nombre" }
Guardar
