<#
.SYNOPSIS
    PowerShell automation helper providing native Windows equivalents for all Makefile targets.

.DESCRIPTION
    Usage:
        .\run.ps1 test
        .\run.ps1 test-concurrency
        .\run.ps1 lint
        .\run.ps1 format
        .\run.ps1 seed
        .\run.ps1 concurrency-demo
        .\run.ps1 failure-drill
        .\run.ps1 restore-drill
        .\run.ps1 rollback-drill
        .\run.ps1 up
        .\run.ps1 down
        .\run.ps1 ps
        .\run.ps1 logs
#>

param(
    [Parameter(Position=0)]
    [ValidateSet("help", "up", "down", "restart", "logs", "ps", "build", "test", "test-concurrency", "lint", "format", "seed", "backup", "restore", "restore-drill", "rollback", "rollback-drill", "failure-drill", "concurrency-demo", "clean")]
    [string]$Target = "help",

    [Parameter(Position=1)]
    [string]$ImageTag = "ghcr.io/algions/hotel-reservation-api:v1.0.0"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

# Locate Python
$PythonBin = "python"
if (Test-Path "$ProjectRoot\.venv\Scripts\python.exe") {
    $PythonBin = "$ProjectRoot\.venv\Scripts\python.exe"
}

# Locate Bash
$BashBin = "bash"
if (Test-Path "C:\Program Files\Git\bin\bash.exe") {
    $BashBin = "C:\Program Files\Git\bin\bash.exe"
}

$ComposeFile = "$ProjectRoot\deploy\docker-compose.yml"
$ComposeProdFile = "$ProjectRoot\deploy\docker-compose.prod.yml"

switch ($Target) {
    "help" {
        Write-Host "Hotel Reservation API — PowerShell Task Runner" -ForegroundColor Cyan
        Write-Host "Available targets:"
        Write-Host "  .\run.ps1 up                 - Start orchestrated containers"
        Write-Host "  .\run.ps1 down               - Stop and remove containers and volumes"
        Write-Host "  .\run.ps1 restart            - Restart running stack"
        Write-Host "  .\run.ps1 logs               - View aggregated JSON logs"
        Write-Host "  .\run.ps1 ps                 - Inspect container health status"
        Write-Host "  .\run.ps1 test               - Run full Pytest suite with coverage"
        Write-Host "  .\run.ps1 test-concurrency   - Run concurrency test"
        Write-Host "  .\run.ps1 lint               - Run ruff & mypy checks"
        Write-Host "  .\run.ps1 format             - Auto-format code with ruff"
        Write-Host "  .\run.ps1 seed               - Seed inventory and sample bookings"
        Write-Host "  .\run.ps1 concurrency-demo   - Run live concurrency race condition demo"
        Write-Host "  .\run.ps1 failure-drill      - Run DB outage & container restart drill"
        Write-Host "  .\run.ps1 restore-drill      - Run point-in-time database restore drill"
        Write-Host "  .\run.ps1 rollback-drill     - Run release rollback demonstration"
        Write-Host "  .\run.ps1 clean              - Remove temporary caches and databases"
    }

    "up" {
        Write-Host "Starting stack via Docker Compose..." -ForegroundColor Green
        docker compose -f $ComposeFile up -d --build
        Start-Sleep -Seconds 5
        docker compose -f $ComposeFile ps
    }

    "down" {
        Write-Host "Tearing down stack and volumes..." -ForegroundColor Yellow
        docker compose -f $ComposeFile down -v
    }

    "restart" {
        docker compose -f $ComposeFile restart
    }

    "logs" {
        docker compose -f $ComposeFile logs -f
    }

    "ps" {
        docker compose -f $ComposeFile ps
    }

    "build" {
        docker compose -f $ComposeFile build
    }

    "test" {
        Write-Host "Running pytest test suite with coverage..." -ForegroundColor Green
        if (-not (Test-Path "$ProjectRoot\evidence")) { New-Item -ItemType Directory -Path "$ProjectRoot\evidence" | Out-Null }
        & $PythonBin -m pytest --cov=app --cov-report=term-missing --cov-report=html:evidence/coverage_html | Tee-Object -FilePath "$ProjectRoot\evidence\test-output.txt"
    }

    "test-concurrency" {
        Write-Host "Running concurrency acceptance test..." -ForegroundColor Green
        & $PythonBin -m pytest tests/test_concurrency.py -v -s
    }

    "lint" {
        Write-Host "Running ruff check, ruff format check, and mypy..." -ForegroundColor Green
        & $PythonBin -m ruff check .
        & $PythonBin -m ruff format --check .
        & $PythonBin -m mypy app scripts
    }

    "format" {
        Write-Host "Applying ruff automated fixes and formatting..." -ForegroundColor Green
        & $PythonBin -m ruff check --fix .
        & $PythonBin -m ruff format .
    }

    "seed" {
        Write-Host "Seeding database..." -ForegroundColor Green
        & $PythonBin -m scripts.seed
    }

    "concurrency-demo" {
        Write-Host "Executing concurrency demo..." -ForegroundColor Green
        & $BashBin "$ProjectRoot\scripts\concurrency_demo.sh"
    }

    "failure-drill" {
        Write-Host "Executing failure and recovery drill..." -ForegroundColor Green
        & $BashBin "$ProjectRoot\scripts\failure_drill.sh"
    }

    "restore-drill" {
        Write-Host "Executing restore drill..." -ForegroundColor Green
        & $BashBin "$ProjectRoot\scripts\restore_drill.sh"
    }

    "rollback-drill" {
        Write-Host "Executing rollback drill..." -ForegroundColor Green
        & $BashBin "$ProjectRoot\scripts\rollback_drill.sh"
    }

    "clean" {
        Write-Host "Cleaning caches and temporary artifacts..." -ForegroundColor Yellow
        Remove-Item -Path "$ProjectRoot\.pytest_cache", "$ProjectRoot\htmlcov", "$ProjectRoot\build", "$ProjectRoot\dist" -Recurse -Force -ErrorAction SilentlyContinue
        Get-ChildItem -Path $ProjectRoot -Filter "*.db*" | Remove-Item -Force -ErrorAction SilentlyContinue
        Write-Host "Clean complete." -ForegroundColor Green
    }
}

