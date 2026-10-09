@echo off
setlocal
cd /d "%~dp0"
set PYTHONPATH=src
python src\main.py
