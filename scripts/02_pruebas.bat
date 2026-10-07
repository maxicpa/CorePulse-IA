@echo off
setlocal
cd /d "%~dp0.."
py -3.12 -m pytest -q
py -3.12 tools\isy0101_self_check.py
pause
