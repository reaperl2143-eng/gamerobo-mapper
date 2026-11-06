# GameRobo mapper - PC setup / auto-start installer.
# Creates a minimized pythonw.exe shortcut in the current user's Startup folder.
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

Write-Host ""
Write-Host "GameRobo RH-5188 mapper - PC setup" -ForegroundColor Cyan
Write-Host "Folder: $here"
Write-Host ""

# --- locate Python -----------------------------------------------------------
$python = $null
foreach ($cand in @("python", "py")) {
    $cmd = Get-Command $cand -ErrorAction SilentlyContinue
    if ($cmd) { $python = $cmd.Source; break }
}
if (-not $python) {
    Write-Host "Python was not found." -ForegroundColor Red
    Write-Host "Install 64-bit Python 3.12 from python.org and tick 'Add python.exe to PATH'." -ForegroundColor Yellow
    exit 1
}

$pyExe = (& $python -c "import sys; print(sys.executable)" 2>$null)
if ($pyExe) { $python = $pyExe.Trim() }
Write-Host "Python: $python"

# --- required packages -------------------------------------------------------
Write-Host "Installing pygame + hidapi (vgamepad is bundled)..."
& $python -m pip install --disable-pip-version-check --quiet pygame hidapi
if ($LASTEXITCODE -ne 0) {
    Write-Host "pip install failed. Check your internet/Python install." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path (Join-Path $here "vgamepad"))) {
    Write-Host "Bundled vgamepad missing - installing from pip..."
    & $python -m pip install --disable-pip-version-check --quiet vgamepad
}

# --- ViGEmBus driver check ---------------------------------------------------
$bus = Get-PnpDevice -ErrorAction SilentlyContinue |
       Where-Object { $_.FriendlyName -like "*Nefarius Virtual Gamepad*" -and $_.Status -eq "OK" }
if (-not $bus) {
    Write-Host ""
    Write-Host "ViGEmBus is not installed." -ForegroundColor Yellow
    $msi = Join-Path $here "vgamepad\win\vigem\install\x64\ViGEmBusSetup_x64.msi"
    if (Test-Path $msi) {
        Write-Host "Launching the bundled installer (accept the admin prompt)..."
        Start-Process msiexec.exe -ArgumentList "/i `"$msi`" /qb" -Verb RunAs -Wait
        Write-Host "If Windows asks, reboot before using the mapper."
    } else {
        Write-Host "Installer not found at: $msi" -ForegroundColor Red
        Write-Host "Download ViGEmBus from https://github.com/nefarius/ViGEmBus/releases" -ForegroundColor Yellow
    }
} else {
    Write-Host "ViGEmBus: OK"
}

# --- pythonw for a hidden console -------------------------------------------
$pyw = Join-Path (Split-Path $python) "pythonw.exe"
if (-not (Test-Path $pyw)) { $pyw = $python }

# --- startup shortcut --------------------------------------------------------
$startup = [Environment]::GetFolderPath("Startup")
$lnk = Join-Path $startup "GameRobo Mapper.lnk"
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut($lnk)
$s.TargetPath = $pyw
$s.Arguments = '"' + (Join-Path $here "ds2xinput.py") + '"'
$s.WorkingDirectory = $here
$s.WindowStyle = 7          # minimized
$s.Description = "GameRobo RH-5188 -> virtual Xbox 360 pad"
$s.Save()

Write-Host ""
Write-Host "Startup shortcut created:" -ForegroundColor Green
Write-Host "  $lnk"
Write-Host ""
Write-Host "It starts automatically at your next login."
Write-Host "To use it right now, double-click run-mapper.cmd (visible console)."
Write-Host "To stop a hidden instance, run stop-mapper.cmd."
Write-Host ""
