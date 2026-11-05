# Instala los carteles automaticos para TODOS los usuarios de esta PC (administrador y cajero).
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
  icacls $dst /grant '*S-1-5-32-545:(OI)(CI)M' /T /Q | Out-Null
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

  # 4) Usuario de Vendita (solo lectura), cifrado para esta PC
  if (-not (Test-Path "$dst\vendita.dat")) {
    Write-Host "`nEscribi el usuario y la clave de Vendita (el de Claude). No se muestran ni se mandan a nadie." -ForegroundColor Yellow
    $u = Read-Host 'Usuario'
    $c = Read-Host 'Clave' -AsSecureString
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($c))
    Add-Type -AssemblyName System.Security
    $bytes = [Text.Encoding]::UTF8.GetBytes((@{ u = $u; c = $plain } | ConvertTo-Json -Compress))
    $enc = [Security.Cryptography.ProtectedData]::Protect($bytes, $null, 'LocalMachine')
    [IO.File]::WriteAllBytes("$dst\vendita.dat", $enc)
  }
  Ok 'Usuario de Vendita guardado'

  # 5) Primera lectura: guarda los precios de hoy (no imprime nada)
  Write-Host '  ... leyendo precios de Vendita (1 o 2 minutos)'
  & powershell -NoProfile -ExecutionPolicy Bypass -File "$dst\carteles.ps1" -SoloBase
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path "$dst\precios.json")) { Mal 'No pude leer Vendita (usuario o clave mal?). Borra C:\carteles\vendita.dat y volve a correr el instalador.' }
  Ok 'Precios de hoy guardados'

  # 6) Arranque automatico: al iniciar sesion cualquier usuario (cajero o administrador), oculto
  $vbs = "$dst\arrancar.vbs"
  Set-Content $vbs 'CreateObject("WScript.Shell").Run "powershell -NoProfile -ExecutionPolicy Bypass -File C:\carteles\carteles.ps1", 0, False' -Encoding ASCII
  $act = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument "`"$vbs`""
  $trg = New-ScheduledTaskTrigger -AtLogOn
  $grp = (New-Object Security.Principal.SecurityIdentifier 'S-1-5-32-545').Translate([Security.Principal.NTAccount]).Value
  $pri = New-ScheduledTaskPrincipal -GroupId $grp -RunLevel Limited
  $set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
  Register-ScheduledTask -TaskName 'Carteles El Tio' -Action $act -Trigger $trg -Principal $pri -Settings $set -Force | Out-Null
  Start-Process wscript.exe "`"$vbs`""
  Ok 'Arranca solo al iniciar sesion (cajero o administrador)'

  Write-Host "`n  LISTO. Desde ahora cada cambio de precio en Vendita sale impreso en la Brother.`n" -ForegroundColor Green
} catch { Mal $_.Exception.Message }
