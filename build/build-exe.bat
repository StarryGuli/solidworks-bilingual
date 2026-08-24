@echo off
rem Build SWBilingual.exe and swbilingual-cli.exe from source.
rem Requires Python 3.8 or newer on PATH. Nothing else has to be installed
rem beforehand; PyInstaller is fetched here if it is missing.

setlocal
cd /d "%~dp0.."

python --version >nul 2>&1
if errorlevel 1 (
    echo Python was not found on PATH.
    echo Install Python 3.8 or newer from https://www.python.org/downloads/
    echo and tick "Add python.exe to PATH" during setup.
    exit /b 1
)

python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install --upgrade pyinstaller || exit /b 1
)

echo Running the test suite...
python -m unittest discover -s tests || exit /b 1

echo Building executables...
python -m PyInstaller build\swbilingual.spec --noconfirm --distpath dist --workpath build\work || exit /b 1

echo.
echo Done. The executables are in the dist folder:
echo   dist\SWBilingual.exe
echo   dist\swbilingual-cli.exe
endlocal
