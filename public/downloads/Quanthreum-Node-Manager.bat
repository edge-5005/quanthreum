@echo off
setlocal enabledelayedexpansion
title Quanthreum (QTH) Windows Node ^& Validator Studio
cd /d "%~dp0"

:MENU
cls
echo ===============================================================================
echo                QUANTHREUM (QTH) - WINDOWS NODE ^& VALIDATOR TOOL
echo       Post-Quantum (W-OTS+) ^| 100M Total Max Supply ^| Ethereum-Nature QVM
echo ===============================================================================
echo.
echo   [1] Launch Native Windows Desktop GUI Studio (Recommended)
echo   [2] Create New 48-Word QTH Wallet
echo   [3] Restore QTH Wallet from 48 Words
echo   [4] Start Core Blockchain Node (Port 8545 + Web Dashboard)
echo   [5] Start Automated Validator Node (Continuous Block Sealer)
echo   [6] Stake QTH into Quantum Proof-of-Stake Pool
echo   [7] Check Account State ^& Staking Balance
echo   [8] Open Web Explorer ^& Dashboard in Browser
echo   [9] Run Zero-Cost Automated Network Demo
echo   [0] Exit
echo.
echo ===============================================================================
set /p CHOICE="Enter choice (0-9): "

if "%CHOICE%"=="1" goto LAUNCH_GUI
if "%CHOICE%"=="2" goto CREATE_WALLET
if "%CHOICE%"=="3" goto RESTORE_WALLET
if "%CHOICE%"=="4" goto START_NODE
if "%CHOICE%"=="5" goto RUN_VALIDATOR
if "%CHOICE%"=="6" goto STAKE_QTH
if "%CHOICE%"=="7" goto CHECK_ACCOUNT
if "%CHOICE%"=="8" goto OPEN_WEB
if "%CHOICE%"=="9" goto RUN_DEMO
if "%CHOICE%"=="0" goto EXIT
goto MENU

:LAUNCH_GUI
echo.
echo Launching Quanthreum Windows GUI Studio...
start "" "%~dp0Launch-Quanthreum-Studio.bat"
goto DONE

:CREATE_WALLET
echo.
echo --- Creating New 48-Word Post-Quantum QTH Wallet ---
set /p WFILE="Enter wallet filename (default: my_qth_wallet.json): "
if "%WFILE%"=="" set WFILE=my_qth_wallet.json
python "%~dp0quanthreum_cli.py" wallet create --file "%WFILE%"
goto DONE

:RESTORE_WALLET
echo.
echo --- Restore QTH Wallet from 48-Word Seed Phrase ---
set /p PHRASE="Enter 48-word seed phrase: "
set /p WFILE="Save to wallet file (default: restored_wallet.json): "
if "%WFILE%"=="" set WFILE=restored_wallet.json
python "%~dp0quanthreum_cli.py" wallet restore --phrase "%PHRASE%" --file "%WFILE%"
goto DONE

:START_NODE
echo.
echo --- Starting Quanthreum Core Node on Port 8545 ---
echo Press Ctrl+C at any time to stop the node.
echo Web UI will be accessible at http://127.0.0.1:8545
python "%~dp0quanthreum_cli.py" node start --port 8545
goto DONE

:RUN_VALIDATOR
echo.
echo --- Start Automated Continuous Validator Node ---
set /p WFILE="Wallet file to validate with (default: my_qth_wallet.json): "
if "%WFILE%"=="" set WFILE=my_qth_wallet.json
set /p SECS="Block interval in seconds (default: 6): "
if "%SECS%"=="" set SECS=6
python "%~dp0quanthreum_cli.py" validator --wallet "%WFILE%" --interval %SECS%
goto DONE

:STAKE_QTH
echo.
echo --- Stake QTH into Quantum Proof-of-Stake (Q-PoS) ---
set /p WFILE="Wallet file (default: my_qth_wallet.json): "
if "%WFILE%"=="" set WFILE=my_qth_wallet.json
set /p AMT="Amount of QTH to stake (min 10.0): "
if "%AMT%"=="" set AMT=32.0
python "%~dp0quanthreum_cli.py" stake --wallet "%WFILE%" --amount %AMT%
goto DONE

:CHECK_ACCOUNT
echo.
set /p ADDR="Enter Quanthreum Address (0xQTH_...): "
python "%~dp0quanthreum_cli.py" account "%ADDR%"
goto DONE

:OPEN_WEB
echo.
echo Opening Quanthreum Web Explorer in browser...
start http://127.0.0.1:8545
goto DONE

:RUN_DEMO
echo.
echo Running Quanthreum Full Network Verification Demo...
python "%~dp0quanthreum_cli.py" demo
goto DONE

:DONE
echo.
pause
goto MENU

:EXIT
echo Exiting Quanthreum Manager.
exit /b 0
