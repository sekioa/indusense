param([int]$Port = 5000)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw 'Environnement absent. Depuis la racine du dépôt, exécuter uv sync --dev.'
}
$store = Join-Path $projectRoot '.mlflow'
New-Item -ItemType Directory -Force -Path $store | Out-Null
$databasePath = (Join-Path $store 'mlflow.db').Replace('\', '/')
$artifactUri = ([System.Uri]::new((Join-Path $store 'artifacts'))).AbsoluteUri
Write-Host "MLflow : http://127.0.0.1:$Port - Ctrl+C pour arrêter"
& $pythonExe -m mlflow server --backend-store-uri "sqlite:///$databasePath" --default-artifact-root $artifactUri --no-serve-artifacts --host 127.0.0.1 --port $Port --workers 1
exit $LASTEXITCODE
