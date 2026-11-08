# Quanthreum (QTH) - PowerShell Studio Launcher
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Quanthreum (QTH) - Windows Desktop Studio Launcher" -ForegroundColor White
Write-Host "  Post-Quantum W-OTS+ and Ethereum Q-PoS Blockchain" -ForegroundColor DarkGray
Write-Host "============================================================" -ForegroundColor Cyan

$pyw = "$env:LOCALAPPDATA\Programs\Python\Python312\pythonw.exe"
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
$appScript = Join-Path $scriptDir "quanthreum_validator_app.py"

if (Test-Path $pyw) {
    Write-Host "Starting Quanthreum Studio GUI via pythonw..." -ForegroundColor Green
    Start-Process -FilePath $pyw -ArgumentList "`"$appScript`""
} elseif (Test-Path $py) {
    Write-Host "Starting Quanthreum Studio GUI via python..." -ForegroundColor Green
    Start-Process -FilePath $py -ArgumentList "`"$appScript`""
} else {
    Write-Host "Starting via system python..." -ForegroundColor Yellow
    Start-Process -FilePath "python" -ArgumentList "`"$appScript`""
}
