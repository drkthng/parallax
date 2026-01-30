@echo off
REM ============================================================
REM Parallax - Setup Script
REM Run this ONCE to create the environment and install dependencies.
REM ============================================================

setlocal
set VENV_DIR=.venv

echo [INFO] Setting up Parallax environment...

REM --- Check for Python ---
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

REM --- Create Virtual Environment ---
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [INFO] Creating virtual environment in %VENV_DIR%...
    python -m venv %VENV_DIR%
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [INFO] Virtual environment already exists.
)

REM --- Activate and Install ---
echo [INFO] Activating virtual environment...
call %VENV_DIR%\Scripts\activate.bat

echo [INFO] Installing/Updating dependencies from requirements.txt...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Setup complete!
echo [INFO] You can now run the app using 'run_parallax.bat'.
echo.
pause
endlocal
