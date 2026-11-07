# Carteles automaticos - Supermercado El Tio. Lo instala INSTALAR.bat en C:\carteles.
# Cada 15 min (7 a 22 h) lee Vendita (SOLO LECTURA), arma el PDF de los productos que cambiaron de precio
# Corre como tarea 'Carteles El Tio' al prender la PC con el usuario administrador (NO como SYSTEM: Edge no arma el PDF),
# y cada 30 s imprime en la Brother lo que haya en C:\carteles\pendientes (tambien PDFs puestos a mano).
# Buzon: cada 2 min mira la carpeta buzon/ de la rama carteles-buzon en GitHub (ahi Claude deja carteles de oferta)
# y baja a pendientes los PDF nuevos. Si el nombre termina en __EAN1_EAN2.pdf, esos productos no llevan cartel blanco ese dia.
param([switch]$SoloBase)
$ErrorActionPreference = 'Stop'
try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch {}
$dir     = 'C:\carteles'
$B       = 'https://gestion.venditaenlinea.com'
$estado  = "$dir\precios.json"
$work    = "$dir\auto"
$pend    = "$dir\pendientes"
$imp     = "$dir\impresos"
$revisar = "$dir\revisar"
$log     = "$dir\registro.txt"
$sumatra = "$dir\SumatraPDF.exe"
$buzonApi = 'https://api.github.com/repos/tobias131313/tienda-el-tio/contents/buzon?ref=carteles-buzon'
$buzonReg = "$dir\buzon.txt"
$script:buzonEan = @{}
function Log($m) { Add-Content $log ("{0:yyyy-MM-dd HH:mm} [{1}] {2}" -f (Get-Date), $env:USERNAME, $m); Write-Host $m }
function Buzon {
  $r = Invoke-WebRequest $buzonApi -UseBasicParsing -TimeoutSec 60 -Headers @{ 'User-Agent' = 'carteles-el-tio'; 'Cache-Control' = 'no-cache' }
  $items = @([Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray()) | ConvertFrom-Json | Where-Object { $_.type -eq 'file' -and $_.name -like '*.pdf' })
  $hechos = @{}; if (Test-Path $buzonReg) { Get-Content $buzonReg | ForEach-Object { $hechos[$_.Trim()] = 1 } }
  $hoy = Get-Date -Format 'yyyy-MM-dd'
  foreach ($it in $items) {
    # EAN con oferta de hoy: no se les hace cartel blanco
    if ($it.name -like "$hoy*" -and $it.name -match '__([0-9_]+)\.pdf$') { $Matches[1].Split('_') | Where-Object { $_ } | ForEach-Object { $script:buzonEan[$_] = $hoy } }
    if ($hechos.ContainsKey($it.name)) { continue }
    $tmp = Join-Path $env:TEMP $it.name
    Invoke-WebRequest $it.download_url -OutFile $tmp -UseBasicParsing -TimeoutSec 120 -Headers @{ 'User-Agent' = 'carteles-el-tio' }
    if ((Get-Item $tmp).Length -lt 2000) { throw "PDF del buzon vacio: $($it.name)" }
    Move-Item $tmp (Join-Path $pend ("Buzon_" + $it.name)) -Force
    Add-Content $buzonReg $it.name
    Log "Buzon: bajado $($it.name)"
  }
}

function Generar([switch]$SoloBase) {
  function Json($url, $hdr, $body) {
    $p = @{ Uri = $url; UseBasicParsing = $true; TimeoutSec = 180 }
    if ($hdr)  { $p.Headers = $hdr }
    if ($body) { $p.Method = 'Post'; $p.Body = [Text.Encoding]::UTF8.GetBytes($body); $p.ContentType = 'application/json' }
    for ($i = 1; $i -le 4; $i++) {
      try { $r = Invoke-WebRequest @p; return ([Text.Encoding]::UTF8.GetString($r.RawContentStream.ToArray()) | ConvertFrom-Json) }
      catch { if ($i -eq 4) { throw }; Start-Sleep -Seconds ([math]::Pow(2, $i)) }
    }
  }

  $cr = Get-Content "$dir\vendita.json" -Raw | ConvertFrom-Json
  $tok = (Json "$B/api/cuentas/login" $null (@{ UserName = $cr.u; Password = $cr.c; RolId = '1' } | ConvertTo-Json)).token
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
  $hoy = Get-Date -Format 'yyyy-MM-dd'
  $salteo = @($cambios | Where-Object { $_.ean -and $script:buzonEan[$_.ean] -eq $hoy })
  if ($salteo.Count) { Log ("Sin cartel blanco (tienen oferta en el buzon): " + (($salteo | ForEach-Object { $_.nombre }) -join ', ')) }
  $cambios = @($cambios | Where-Object { -not ($_.ean -and $script:buzonEan[$_.ean] -eq $hoy) })
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
  $a = @('--headless=new', '--disable-gpu', '--no-sandbox', '--no-first-run', '--no-pdf-header-footer', '--virtual-time-budget=8000',
         "--user-data-dir=`"$env:TEMP\carteles-edge`"", "--print-to-pdf=`"$tmp`"", $url)
  $pr = Start-Process $edge -ArgumentList $a -PassThru -WindowStyle Hidden
  $null = $pr.WaitForExit(120000)
  # Edge a veces termina el proceso principal antes de escribir el PDF: esperar hasta 90 s a que aparezca y deje de crecer
  $prev = -1
  for ($i = 0; $i -lt 45; $i++) {
    Start-Sleep -Seconds 2
    if (Test-Path $tmp) { $len = (Get-Item $tmp).Length; if ($len -gt 2000 -and $len -eq $prev) { break }; $prev = $len }
  }
  if (-not (Test-Path $tmp) -or (Get-Item $tmp).Length -lt 2000) { throw "El PDF salio vacio (Edge: $edge)" }

  if ($cambios.Count -gt 300) { Move-Item $tmp (Join-Path $revisar $nombre) -Force; Log "$($cambios.Count) cambios: PDF en revisar (no se imprime solo)" }
  else { Move-Item $tmp (Join-Path $pend $nombre) -Force; Log "$($cambios.Count) carteles a imprimir: $nombre" }

  Guardar
}

if ($SoloBase) { try { Generar -SoloBase; exit 0 } catch { Log "ERROR base: $($_.Exception.Message)"; exit 1 } }

$impresora = (Get-Content "$dir\impresora.txt" -Raw).Trim()
Log "Arranca (impresora: $impresora)"
$ultGen = [datetime]::MinValue
$ultBuzon = [datetime]::MinValue
while ($true) {
  $ahora = Get-Date
  if (($ahora - $ultBuzon).TotalMinutes -ge 2) {
    try { Buzon } catch { Log "ERROR buzon: $($_.Exception.Message)" }
    $ultBuzon = $ahora
  }
  if (($ahora - $ultGen).TotalMinutes -ge 15 -and $ahora.Hour -ge 7 -and $ahora.Hour -lt 22) {
    try { Generar } catch { Log "ERROR al generar: $($_.Exception.Message)" }
    $ultGen = $ahora
  }
  Get-ChildItem $pend -Filter *.pdf -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddSeconds(-10) } |
    ForEach-Object {
      try {
        $a = @('-print-to', "`"$impresora`"", '-print-settings', 'noscale', '-silent', "`"$($_.FullName)`"")
        $p = Start-Process $sumatra -ArgumentList $a -PassThru -WindowStyle Hidden
        if (-not $p.WaitForExit(120000)) { $p.Kill(); throw 'la impresion no termino' }
        if ($p.ExitCode -ne 0) { throw "codigo $($p.ExitCode)" }
        Move-Item $_.FullName (Join-Path $imp ("{0:yyyy-MM-dd_HHmm}_{1}" -f (Get-Date), $_.Name)) -Force
        Log "Impreso: $($_.Name)"
      } catch { Log "ERROR al imprimir $($_.Name): $($_.Exception.Message) (reintenta en 30 s)" }
    }
  Start-Sleep -Seconds 30
}
