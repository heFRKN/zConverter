# Builds dist\zConventer\zConventer.exe and a release zip.
# Usage:  powershell -ExecutionPolicy Bypass -File build.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) { python -m venv .venv }
$py = ".\.venv\Scripts\python.exe"
& $py -m pip install --upgrade pip | Out-Null
& $py -m pip install -r requirements.txt -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

& $py tools\make_icon.py
& $py -m PyInstaller zConventer.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

$version = (Select-String -Path zconventer\__init__.py -Pattern '__version__ = "(.+)"').Matches[0].Groups[1].Value
$zip = "dist\zConventer-$version-windows-x64.zip"
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path dist\zConventer -DestinationPath $zip
Write-Host "OK -> dist\zConventer\zConventer.exe"
Write-Host "OK -> $zip"
