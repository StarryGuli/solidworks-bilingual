@echo off
rem Open a command prompt with the tool ready to use.
setlocal
cd /d "%~dp0"
echo SOLIDWORKS bilingual language pack builder
echo.
python swbilingual-cli.py --help
echo.
cmd /k
endlocal
