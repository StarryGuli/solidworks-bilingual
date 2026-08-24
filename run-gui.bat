@echo off
rem Start the desktop interface from source. Requires Python 3.8 or newer.
setlocal
cd /d "%~dp0"
python swbilingual-gui.py %*
if errorlevel 1 pause
endlocal
