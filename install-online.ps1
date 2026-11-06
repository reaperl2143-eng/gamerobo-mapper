# GameRobo RH-5188 online installer.
# Usage (PowerShell):
#   powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/reaperl2143-eng/gamerobo-mapper/main/install-online.ps1 | iex"
$ErrorActionPreference = "Stop"

$repo    = "reaperl2143-eng/gamerobo-mapper"
$branch  = "main"
$target  = "E:\GameRobo"
$archive = "https://github.com/$repo/archive/refs/heads/$branch.zip"

Write-Host ""
Write-Host "GameRobo RH-5188 mapper installer" -ForegroundColor Cyan
Write-Host "Target: $target"
Write-Host ""

if (-not (Test-Path "E:\")) {
    Write-Host "E:\ was not found. Install to another drive by editing `$target in this script." -ForegroundColor Red
    exit 1
}

# --- Python -----------------------------------------------------------------
$python = $null
foreach ($cand in @("python", "py")) {
    $cmd = Get-Command $cand -ErrorAction SilentlyContinue
    if ($cmd) { $python = $cmd.Source; break }
}
if (-not $python) {
    Write-Host "Python was not found." -ForegroundColor Red
    Write-Host "Install 64-bit Python 3.12 from python.org and tick 'Add python.exe to PATH', then rerun." -ForegroundColor Yellow
    exit 1
}
$pyExe = (& $python -c "import sys; print(sys.executable)" 2>$null)
if ($pyExe) { $python = $pyExe.Trim() }
Write-Host "Python: $python"

# --- Download + extract -----------------------------------------------------
$tmp = Join-Path $env:TEMP "gamerobo-src"
$zip = Join-Path $env:TEMP "gamerobo.zip"
if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
Write-Host "Downloading $archive"
Invoke-WebRequest $archive -OutFile $zip -UseBasicParsing
Expand-Archive $zip $tmp -Force

# --- Install to target ------------------------------------------------------
if (Test-Path $target) {
    $bak = "$target.bak-" + (Get-Date -Format "yyyyMMdd-HHmmss")
    Write-Host "Existing install found; moving it to $bak"
    Move-Item $target $bak
}
$src = Join-Path $tmp "gamerobo-mapper-$branch"
Move-Item $src $target
Set-Location $target
Write-Host "Files installed to $target"

# --- Python packages --------------------------------------------------------
Write-Host "Installing pygame + hidapi (vgamepad is bundled)..."
& $python -m pip install --disable-pip-version-check --quiet pygame hidapi
if ($LASTEXITCODE -ne 0) {
    Write-Host "pip install failed. Check your internet/Python install." -ForegroundColor Red
    exit 1
}

# --- ViGEmBus ---------------------------------------------------------------
$bus = Get-PnpDevice -ErrorAction SilentlyContinue |
       Where-Object { $_.FriendlyName -like "*Nefarius Virtual Gamepad*" -and $_.Status -eq "OK" }
if (-not $bus) {
    $msi = Join-Path $target "vgamepad\win\vigem\install\x64\ViGEmBusSetup_x64.msi"
    if (Test-Path $msi) {
        Write-Host "ViGEmBus is missing; installing the bundled driver (accept the admin prompt)..."
        Start-Process msiexec.exe -ArgumentList "/i `"$msi`" /qb" -Verb RunAs -Wait
    } else {
        Write-Host "ViGEmBus MSI was not found in the package." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "ViGEmBus: OK"
}

# --- Startup shortcut -------------------------------------------------------
$pyw = Join-Path (Split-Path $python) "pythonw.exe"
if (-not (Test-Path $pyw)) { $pyw = $python }
$startup = [Environment]::GetFolderPath("Startup")
$lnk = Join-Path $startup "GameRobo Mapper.lnk"
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut($lnk)
$s.TargetPath = $pyw
$s.Arguments = '"' + (Join-Path $target "ds2xinput.py") + '"'
$s.WorkingDirectory = $target
$s.WindowStyle = 7
$s.Description = "GameRobo RH-5188 -> virtual Xbox 360 pad"
$s.Save()
Write-Host "Startup shortcut created: $lnk"

# --- Verify -----------------------------------------------------------------
Write-Host "Testing the virtual pad..."
& $python -c "import vgamepad as vg, time; p=vg.VX360Gamepad(); time.sleep(0.5); print('virtual Xbox pad OK')"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Virtual pad test failed. If ViGEmBus was just installed, reboot and test again." -ForegroundColor Yellow
    exit 2
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "Test now:   $target\run-mapper.cmd"
Write-Host "Stop:       $target\stop-mapper.cmd"
Write-Host "Autostart:  created in your Startup folder (works after next login)."
Write-Host ""
