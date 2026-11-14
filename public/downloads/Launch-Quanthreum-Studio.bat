@echo off
setlocal EnableDelayedExpansion
title Quanthreum Studio Launcher
cd /d "%~dp0"

echo ============================================================
echo   Quanthreum (QTH) - Windows Desktop Studio Launcher
echo   Post-Quantum W-OTS+ and Ethereum Q-PoS Blockchain
echo ============================================================
echo.

set "PY_BIN="

:: Check 1: User AppData Python 3.12 (Direct path)
if exist "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" (
    set "PY_BIN=%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
    goto LAUNCH
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PY_BIN=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    goto LAUNCH
)

:: Check 2: pythonw in PATH
for /f "delims=" %%I in ('where pythonw 2^>nul') do (
    set "PY_BIN=%%I"
    goto LAUNCH
)

:: Check 3: python in PATH
for /f "delims=" %%I in ('where python 2^>nul') do (
    set "PY_BIN=%%I"
    goto LAUNCH
)

:: Check 4: py launcher
for /f "delims=" %%I in ('where py 2^>nul') do (
    set "PY_BIN=%%I"
    goto LAUNCH
)

echo [ERROR] Python was not found in PATH or standard installation directory.
echo Please install Python 3.10+ from https://www.python.org/ or add Python to PATH.
echo.
pause
exit /b 1

:LAUNCH
echo Found Python at: "!PY_BIN!"
echo Starting Quanthreum Windows Studio...
echo.

start "" "!PY_BIN!" "%~dp0quanthreum_validator_app.py"
if errorlevel 1 (
    echo [ERROR] Failed to start studio with pythonw. Retrying with python...
    python "%~dp0quanthreum_validator_app.py"
)

exit /b 0
