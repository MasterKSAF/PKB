Param(
    [string]$PgBin = "C:\Program Files\PostgreSQL\17\bin",
    [string]$DbName = "neuroassistant",
    [string]$DbUser = "postgres",
    [string]$DbPassword = "postgres",
    [string]$DbHost = "localhost",
    [int]$DbPort = 5432
)

$ErrorActionPreference = "Stop"

function Resolve-PsqlPath {
    Param([string]$PgBin)
    $psql = Join-Path $PgBin "psql.exe"
    if (Test-Path $psql) {
        return $psql
    }
    $cmd = Get-Command psql -ErrorAction SilentlyContinue
    if ($null -ne $cmd) {
        return $cmd.Source
    }
    throw "psql.exe not found. Set -PgBin or add psql to PATH."
}

function Ensure-Database {
    Param(
        [string]$PsqlPath,
        [string]$DbName,
        [string]$DbUser,
        [string]$DbPassword,
        [string]$DbHost,
        [int]$DbPort
    )

    $env:PGPASSWORD = $DbPassword
    $exists = & $PsqlPath `
        -h $DbHost -p $DbPort -U $DbUser -d postgres `
        -tAc "SELECT 1 FROM pg_database WHERE datname='${DbName}'"

    if ($exists -match "1") {
        return
    }

    Write-Host "Creating database '$DbName'..."
    & $PsqlPath -h $DbHost -p $DbPort -U $DbUser -d postgres `
        -c "CREATE DATABASE ${DbName};"
}

$psqlPath = Resolve-PsqlPath -PgBin $PgBin

Ensure-Database `
    -PsqlPath $psqlPath `
    -DbName $DbName `
    -DbUser $DbUser `
    -DbPassword $DbPassword `
    -DbHost $DbHost `
    -DbPort $DbPort

$schemaPath = (Resolve-Path (Join-Path $PSScriptRoot "..\\schema_postgres.sql")).Path

$dbUrlPsql = "postgresql://$DbUser@$DbHost`:$DbPort/$DbName"
$dbUrlApp = "postgresql+psycopg://$DbUser@$DbHost`:$DbPort/$DbName"

Write-Host "Applying schema from $schemaPath ..."
$env:PGPASSWORD = $DbPassword
& $psqlPath $dbUrlPsql -f $schemaPath

Write-Host "Starting API with DATABASE_URL=$dbUrlApp ..."
$env:DATABASE_URL = $dbUrlApp

Push-Location (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
try {
    python -m uvicorn neuroassistant.api.app:app --reload
} finally {
    Pop-Location
}

