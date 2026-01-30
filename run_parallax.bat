@echo off
REM ============================================================
REM Parallax - Windowless Launcher
REM - Auto-stops existing instances
REM - Starts Solara in background (no window)
REM - Logs to parallax.log
REM - Launches Browser App
REM ============================================================

setlocal enabledelayedexpansion

REM --- Configuration ---
set VENV_DIR=.venv
set SOLARA_PORT=8501
set LOG_FILE=parallax.log
set MAX_RETRIES=30

REM --- Check for Environment ---
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found.
    echo [TIP] Please run 'setup.bat' first.
    pause
    exit /b 1
)

REM --- Auto-Stop Existing Instance ---
call stop_parallax.bat >nul 2>&1

REM --- Start Solara Server (Minimized) ---
echo [INFO] Starting Solara server (Minimized Window)...
echo [INFO] Logs redirected to %LOG_FILE%

REM Use start /MIN with cmd to redirect logs reliably
start "ParallaxServer" /MIN cmd /c "%VENV_DIR%\Scripts\python.exe -m solara run src/app.py --port %SOLARA_PORT% --no-open > %LOG_FILE% 2>&1"

REM --- Smart Wait for Port (PowerShell TCP Check) ---
echo [INFO] Waiting for server to be ready...
powershell -Command "$i=0; while ($i -lt %MAX_RETRIES%) { try { $t = New-Object Net.Sockets.TcpClient; $t.Connect('127.0.0.1', %SOLARA_PORT%); $t.Close(); exit 0 } catch { Start-Sleep -Milliseconds 1000; $i++ } }; exit 1"

if %ERRORLEVEL% equ 0 (
    goto :LaunchBrowser
)

:LaunchBrowser
echo [INFO] Server Ready! Launching App...
start "" "msedge" --app=http://localhost:%SOLARA_PORT% 2>nul || start "" "chrome" --app=http://localhost:%SOLARA_PORT% 2>nul || start "" http://localhost:%SOLARA_PORT%
goto :EOF

REM --- Exit Launcher ---
REM This closes the CLI window immediately, leaving the app running.
exit
