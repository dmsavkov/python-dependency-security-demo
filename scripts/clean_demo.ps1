# Remove local artifacts produced by running the exercises.
# Safe to re-run. Does not touch exercise source files.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Cleaning demo artifacts under $Root"

$dirs = @(
    ".venv-tools", ".venv-safety", ".venv-ex2", ".venv-ex3", ".venv-ex4", ".venv-ex5",
    "ex3_hashes\dl",
    "ex4_install_time\dist",
    "ex5_confusion_typosquatting\indexes"
)
foreach ($d in $dirs) {
    if (Test-Path $d) {
        Remove-Item -Recurse -Force $d
        Write-Host "  removed $d"
    }
}

$files = @(
    "ex1_known_vulns\req-fixme.txt",
    "ex1_known_vulns\report.json",
    "ex1_known_vulns\.safety-project.ini",
    "ex3_hashes\requirements-tampered.txt"
)
foreach ($f in $files) {
    if (Test-Path $f) {
        Remove-Item -Force $f
        Write-Host "  removed $f"
    }
}

$proof = Join-Path $env:TEMP "PROOF_setup_py_was_executed.txt"
if (Test-Path $proof) {
    Remove-Item -Force $proof
    Write-Host "  removed $proof"
}

Write-Host "Done. Re-create tool venvs with the README setup section when you need them again."
