# migrate.ps1 - PowerShell migration runner for PostgreSQL
# Usage:
#   .\migrate.ps1 -DatabaseUrl "postgresql://user:pass@localhost:5432/dbname"
#   OR set env vars: DB_HOST, DB_PORT, DB_USER, DB_NAME, DB_PASSWORD

param(
    [string]$DatabaseUrl = ""
)

$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$migrations = Get-ChildItem -Path "$ScriptDir/migrations" -Filter *.sql | Sort-Object Name

if ($DatabaseUrl) {
    Write-Host "Applying migrations using DATABASE_URL: $DatabaseUrl"
    foreach ($migration in $migrations) {
        Write-Host "---- applying: $($migration.FullName)"
        psql "$DatabaseUrl" -f $migration.FullName
    }
    Write-Host "All migrations applied."
    exit 0
}

# Use environment variables
$DB_HOST = $env:DB_HOST
$DB_PORT = $env:DB_PORT
$DB_USER = $env:DB_USER
$DB_NAME = $env:DB_NAME
$DB_PASSWORD = $env:DB_PASSWORD

if (-not $DB_HOST -or -not $DB_PORT -or -not $DB_USER -or -not $DB_NAME -or -not $DB_PASSWORD) {
    Write-Host "Usage: .\\migrate.ps1 -DatabaseUrl <DATABASE_URL> OR set DB_HOST, DB_PORT, DB_USER, DB_NAME, DB_PASSWORD env vars"
    exit 1
}

Write-Host "Running migrations on $DB_NAME as $DB_USER at $DB_HOST $DB_PORT..."
$env:PGPASSWORD = $DB_PASSWORD
foreach ($migration in $migrations) {
    Write-Host "Applying $($migration.FullName)..."
    psql -v ON_ERROR_STOP=1 -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $migration.FullName
}
Remove-Item Env:PGPASSWORD
Write-Host "Migrations complete."
