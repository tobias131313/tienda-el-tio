@echo off
rem Instalador de carteles automaticos - Supermercado El Tio
rem Pide permiso de administrador y corre instalar.ps1
net session >nul 2>&1
if %errorlevel% neq 0 (
  powershell -Command "Start-Process '%~f0' -Verb RunAs"
  exit /b
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar.ps1"
pause
