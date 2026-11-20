# AuraBell Stop Script
# Safely stop all AuraBell services without destroying data

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendPath = Join-Path -Path $ProjectRoot -ChildPath "backend"

function Write-Info([string]$message) {
    Write-Host "[INFO] $message" -ForegroundColor Green
}

function Write-Warning([string]$message) {
    Write-Host "[WARNING] $message" -ForegroundColor Yellow
}

function Write-Error([string]$message) {
    Write-Host "[ERROR] $message" -ForegroundColor Red
}

function Stop-AllServices {
    Write-Info "Stopping all AuraBell services..."
    
    # Stop Docker services (without removing volumes)
    try {
        Write-Info "Stopping Docker services..."
        & docker compose -f "$BackendPath\docker-compose.yml" down
        Write-Info "Docker services stopped successfully."
    }
    catch {
        Write-Warning "Could not stop Docker services: $($_.Exception.Message)"
    }
    
    Write-Info "All services stopped. Docker volumes and data preserved."
}

function Main {
    param(
        [switch]$Force
    )
    
    if ($Force) {
        Write-Warning "FORCE STOP requested. This will stop running containers but preserve volumes."
    }
    
    Stop-AllServices
}

Main
