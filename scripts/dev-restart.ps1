#!/usr/bin/env pwsh
# AuraBell Restart Script
# Restart all AuraBell services (stop + start)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendPath = Join-Path -Path $ProjectRoot -ChildPath "backend"
$FrontendPath = Join-Path -Path $ProjectRoot -ChildPath "frontend"

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

function Start-DockerServices {
    Write-Info "Starting Docker services..."

    # Check if Docker is available
    try {
        $null = docker version
    }
    catch {
        Write-Error "Docker is not available. Please install Docker or run services manually."
        return $false
    }

    # Start Docker services
    try {
        Write-Info "Building and starting Docker services..."
        & docker compose -f "$BackendPath\docker-compose.yml" build
        & docker compose -f "$BackendPath\docker-compose.yml" up -d

        Write-Info "Docker services started successfully."
        return $true
    }
    catch {
        Write-Error "Failed to start Docker services: $($_.Exception.Message)"
        return $false
    }
}

function Start-Backend {
    Write-Info "Starting backend service..."

    # Check if .env file exists
    $envFile = Join-Path -Path $BackendPath -ChildPath ".env"
    if (-not (Test-Path $envFile)) {
        Write-Warning ".env file not found. Copying from .env.example..."
        Copy-Item "$BackendPath\.env.example" $envFile
    }

    # Start backend with Docker
    try {
        Write-Info "Starting backend with Docker..."
        & docker compose -f "$BackendPath\docker-compose.yml" up -d backend
        Write-Info "Backend started successfully."
        return $true
    }
    catch {
        Write-Error "Failed to start backend: $($_.Exception.Message)"
        return $false
    }
}

function Start-Frontend {
    Write-Info "Starting frontend service..."

    # Check if Node.js is available
    try {
        $null = node --version
        $null = npm --version
    }
    catch {
        Write-Error "Node.js or npm not found. Please install Node.js to run frontend."
        return $false
    }

    # Install dependencies if needed
    $packageJson = Join-Path -Path $FrontendPath -ChildPath "package.json"
    $nodeModules = Join-Path -Path $FrontendPath -ChildPath "node_modules"
    if (-not (Test-Path $nodeModules)) {
        Write-Info "Installing frontend dependencies..."
        Push-Location $FrontendPath
        try {
            & npm install
            Write-Info "Frontend dependencies installed."
        }
        catch {
            Pop-Location
            Write-Error "Failed to install frontend dependencies: $($_.Exception.Message)"
            return $false
        }
        Pop-Location
    }

    # Start frontend
    try {
        Write-Info "Starting frontend..."
        Push-Location $FrontendPath
        $frontendProcess = Start-Process -FilePath "npm" -ArgumentList "dev" -PassThru -NoNewWindow
        Pop-Location

        Write-Info "Frontend started successfully."
        return $true
    }
    catch {
        Pop-Location
        Write-Error "Failed to start frontend: $($_.Exception.Message)"
        return $false
    }
}

function Restart-AllServices {
    Write-Info "Restarting all AuraBell services..."
    Stop-AllServices
    if (Start-DockerServices) {
        if (Start-Backend) {
            Start-Frontend
        }
    }
}

Restart-AllServices