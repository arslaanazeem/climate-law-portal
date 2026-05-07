@echo off
REM ============================================================================
REM   Climate Law Intelligence Portal - One-click local launcher
REM
REM   Double-click this file. It will:
REM     1. Verify Python is installed
REM     2. Create a virtual environment ^(.venv^) on first run
REM     3. Install dependencies
REM     4. Apply database migrations
REM     5. Import the 5,000 cases on first run only
REM     6. Open your browser
REM     7. Start the web server at http://127.0.0.1:8000/
REM
REM   Press Ctrl+C in this window to stop the server.
REM ============================================================================

cd /d "%~dp0"
title Climate Law Portal - Local Server
color 0A
cls

echo.
echo  ==========================================================
echo    Climate Law Intelligence Portal - Pakistan
echo    One-click local launcher
echo  ==========================================================
echo.

REM -------------------------------------------------------------------- 1. Python
echo [1/6] Checking Python...
where python >nul 2>nul
if errorlevel 1 goto :err_python

for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo       Found: %%v

REM -------------------------------------------------------------------- 2. Venv
echo.
echo [2/6] Setting up virtual environment...
if exist ".venv\Scripts\python.exe" goto :venv_ready

echo       Creating .venv [first run, takes about 10 seconds]...
python -m venv .venv
if errorlevel 1 goto :err_venv
goto :venv_done

:venv_ready
echo       Already exists - reusing.

:venv_done
call ".venv\Scripts\activate.bat"

REM -------------------------------------------------------------------- 3. Deps
echo.
echo [3/6] Installing Python packages...
python -m pip install --upgrade pip --quiet --disable-pip-version-check
python -m pip install -r requirements.txt --quiet --disable-pip-version-check
if errorlevel 1 goto :err_pip
echo       Done.

REM -------------------------------------------------------------------- 4. DB
echo.
echo [4/6] Applying database migrations...
python manage.py migrate --noinput
if errorlevel 1 goto :err_migrate

REM -------------------------------------------------------------------- 5. Data
echo.
echo [5/6] Checking case database...
set CASE_COUNT=0
for /f %%c in ('python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'climate_law_portal.settings'); django.setup(); from cases.models import Case; print(Case.objects.count())" 2^>nul') do set CASE_COUNT=%%c

if "%CASE_COUNT%"=="0" goto :do_ingest
echo       Database already has %CASE_COUNT% cases - skipping import.
goto :start_server

:do_ingest
echo       Database is empty. Importing 5,000 cases - takes about a minute...
python manage.py ingest_cases
if errorlevel 1 goto :err_ingest

REM -------------------------------------------------------------------- 6. Server
:start_server
echo.
echo [6/6] Starting web server...

REM Pick the first port the OS will let us bind to.
REM Windows with Hyper-V/WSL sometimes reserves 8000; we fall back automatically.
set PORT=8000
for /f %%p in ('python _pick_port.py 2^>nul') do set PORT=%%p
if "%PORT%"=="0" goto :err_port

echo       Using http://127.0.0.1:%PORT%/
echo.
echo  ==========================================================
echo    The site is starting. Your browser will open shortly.
echo    Press Ctrl+C in THIS window to stop the server.
echo  ==========================================================
echo.

start "" "http://127.0.0.1:%PORT%/"

python manage.py runserver 127.0.0.1:%PORT%

echo.
echo Server stopped. You can close this window.
pause
exit /b 0


REM ============================================================================
REM Error handlers
REM ============================================================================

:err_python
color 0C
echo.
echo  ERROR: Python is not installed or not on your PATH.
echo.
echo  1. Download Python 3.10+ from:  https://www.python.org/downloads/
echo  2. During install, tick the box  "Add Python to PATH"
echo  3. Close this window, restart your computer, run this file again.
echo.
pause
exit /b 1

:err_venv
color 0C
echo.
echo  ERROR: Could not create the virtual environment.
echo  Try running this script from a folder you have write access to.
echo.
pause
exit /b 1

:err_pip
color 0C
echo.
echo  ERROR: Dependency installation failed.
echo  Make sure you have an internet connection and try again.
echo.
pause
exit /b 1

:err_migrate
color 0C
echo.
echo  ERROR: Database migration failed.
echo  See the error messages above for details.
echo.
pause
exit /b 1

:err_ingest
color 0C
echo.
echo  ERROR: Case import failed.
echo  Verify that the all_text_cases\ folder exists next to this file.
echo.
pause
exit /b 1

:err_port
color 0C
echo.
echo  ERROR: Could not find any free TCP port to bind to.
echo  This is unusual. Check whether a firewall, antivirus, or
echo  Hyper-V port reservation is blocking ports 8000, 8765, 8080, 8888.
echo.
echo  To see Windows port reservations:
echo      netsh interface ipv4 show excludedportrange tcp
echo.
pause
exit /b 1
