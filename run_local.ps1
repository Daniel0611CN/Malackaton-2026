# Ejecuta los escenarios en Windows (PowerShell).
#   .\run_local.ps1                      -> ambos escenarios, navegador visible
#   .\run_local.ps1 -Test tests/test_scenario2_insufficient_balance.py
#   .\run_local.ps1 -Game "Lucky Drums 88"     -> otro juego (nombre tal y como se ve en la tarjeta)
param(
    [string]$Market = "betsson_com",
    [string]$Test = "tests",
    [string]$Headless = "0",
    [string]$Game = ""
)
$env:TARGET_MARKET = $Market
$env:HEADLESS = $Headless
if ($Game) { $env:GAME_NAME = $Game } else { Remove-Item Env:GAME_NAME -ErrorAction SilentlyContinue }
python -m pytest $Test
python scripts/build_report.py reports
Write-Host "Informe: reports\index.html"
