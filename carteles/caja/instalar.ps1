# Instala los carteles automaticos en esta PC: corre como tarea del sistema, para cualquier usuario (administrador o cajero).
# Corre en PowerShell como administrador. Deja todo en C:\carteles.
$ErrorActionPreference = 'Stop'
function Ok($m)  { Write-Host "  OK  $m" -ForegroundColor Green }
function Mal($m) { Write-Host "  ERROR  $m" -ForegroundColor Red; Read-Host 'Mandale una foto de esto a Claude y apreta Enter'; exit 1 }
$src = $PSScriptRoot
$dst = 'C:\carteles'
Write-Host "`nInstalando carteles automaticos`n" -ForegroundColor Cyan
try {
  # 1) Archivos en C:\carteles, con permiso de escritura para todos los usuarios
  New-Item -ItemType Directory -Force $dst, "$dst\auto", "$dst\pendientes", "$dst\impresos", "$dst\revisar" | Out-Null
  Copy-Item "$src\carteles.ps1" $dst -Force
  Copy-Item "$src\auto\*" "$dst\auto" -Recurse -Force
  Ok 'Archivos copiados en C:\carteles'

  # 2) SumatraPDF (imprime PDF sin abrir ventanas): se instala aparte desde su pagina oficial; aca se copia a C:\carteles
  $sum = "$dst\SumatraPDF.exe"
  if (-not (Test-Path $sum)) {
    $cand = @("$env:LOCALAPPDATA\SumatraPDF\SumatraPDF.exe", "$env:ProgramFiles\SumatraPDF\SumatraPDF.exe", "${env:ProgramFiles(x86)}\SumatraPDF\SumatraPDF.exe") +
            @(Get-ChildItem "$env:USERPROFILE\Downloads" -Filter 'SumatraPDF*.exe' -ErrorAction SilentlyContinue | Where-Object { $_.Name -notlike '*install*' } | ForEach-Object FullName)
    $f = $cand | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
    if (-not $f) { Mal 'Falta SumatraPDF. Instalalo desde https://www.sumatrapdfreader.org y volve a correr esto.' }
    Copy-Item $f $sum -Force
  }
  Ok 'SumatraPDF listo'

  # 3) Impresora Brother (la de tickets y la predeterminada no se tocan)
  $bro = @(Get-Printer | Where-Object { $_.Name -like '*Brother*' -and $_.Name -notlike '*Fax*' })
  if ($bro.Count -eq 0) { Mal 'No encuentro la Brother. Fijate que este prendida y conectada por USB, y volve a correr el instalador.' }
  $pref = @($bro | Where-Object { $_.PortName -like 'USB*' }) + $bro
  $imp = $pref[0].Name
  Set-Content "$dst\impresora.txt" $imp -Encoding UTF8
  Ok "Impresora: $imp"

  # 4) Usuario de Vendita (solo lectura). Archivo que solo pueden abrir el sistema y los administradores (el cajero no)
  $vf = "$dst\vendita.json"
  if (-not (Test-Path $vf)) {
    Write-Host "`nEscribi el usuario y la clave de Vendita (el de Claude). Quedan en esta PC, el cajero no los puede ver." -ForegroundColor Yellow
    $u = Read-Host 'Usuario'
    $c = Read-Host 'Clave' -AsSecureString
    $plain = (New-Object System.Net.NetworkCredential('', $c)).Password
    Set-Content $vf (@{ u = $u; c = $plain } | ConvertTo-Json -Compress) -Encoding UTF8
  }
  icacls $vf /inheritance:r /grant:r '*S-1-5-18:F' '*S-1-5-32-544:F' /Q | Out-Null
  Ok 'Usuario de Vendita guardado'

  # 5) Primera lectura: guarda los precios de hoy (no imprime nada)
  Write-Host '  ... leyendo precios de Vendita (1 o 2 minutos)'
  & powershell -NoProfile -ExecutionPolicy Bypass -File "$dst\carteles.ps1" -SoloBase
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path "$dst\precios.json")) { Mal 'No pude leer Vendita (usuario o clave mal?). Borra C:\carteles\vendita.json y volve a correr el instalador.' }
  Ok 'Precios de hoy guardados'

  # 6) Arranque automatico: tarea del sistema al prender la PC (no importa que usuario use la caja)
  $act = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File C:\carteles\carteles.ps1'
  $trg = New-ScheduledTaskTrigger -AtStartup
  $pri = New-ScheduledTaskPrincipal -UserId 'S-1-5-18' -LogonType ServiceAccount -RunLevel Highest
  $set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5)
  Register-ScheduledTask -TaskName 'Carteles El Tio' -Action $act -Trigger $trg -Principal $pri -Settings $set -Force | Out-Null
  Start-ScheduledTask -TaskName 'Carteles El Tio'
  Ok 'Arranca solo al prender la PC (para todos los usuarios)'

  Write-Host "`n  LISTO. Desde ahora cada cambio de precio en Vendita sale impreso en la Brother.`n" -ForegroundColor Green
} catch { Mal $_.Exception.Message }
