@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0link-all.ps1" %*
pause