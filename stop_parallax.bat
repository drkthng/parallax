@echo off
REM ============================================================
REM Parallax - Stop Script
REM Kills the process listening on port 8501.
REM ============================================================

setlocal enabledelayedexpansion
set PORT=8501

echo [INFO] and checking for process on port %PORT%...

REM Get PID of process listening on PORT
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%PORT%" ^| findstr "LISTENING"') do (
    set PID=%%a
)

if defined PID (
    echo [INFO] Found process with PID: !PID!. Killing it...
    taskkill /F /PID !PID! >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        echo [SUCCESS] Process !PID! killed.
    ) else (
        echo [ERROR] Failed to kill process !PID!. It might require Admin privileges.
    )
) else (
    echo [INFO] No process found on port %PORT%.
)

endlocal
