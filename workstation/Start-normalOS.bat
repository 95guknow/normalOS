@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-normalos.ps1" %*
pause