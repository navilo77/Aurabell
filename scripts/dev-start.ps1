#!/usr/bin/env pwsh
# AuraBell One-Click Development Launcher
# Created with safety-first approach

# Configuration
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendPath = Join-Path -Path $ProjectRoot -ChildPath "backend"
$FrontendPath = Join-Path -Path $ProjectRoot -ChildPath "frontend"

# Service tracking
$Global:TrackedProcesses = @{}

function Write-Info([string]$message) {
    Write-Host "[INFO] $message" -ForegroundColor Green
}

function Write-Warning([string]$message) {
    Write-Host "[WARNING] $message" -ForegroundColor Yellow
}

function Write-Error([string]$message) {
    Write-Host "[ERROR] $message" -ForegroundColor Red
}

function Test-Port([int]$port, [string]$serviceName) {
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $client.Connect("localhost", $port)
        $client.Close()
        Write-Warning "$serviceName is already running on port $port"
        return $false
    }
    catch {
        return $true
    }
}

function Test-BackendContainer {
    try {
        $container = docker ps --filter "name=aura-bell-backend" --filter "status=running" --format "{{.Names}}" 2>$null
        return ($container -eq "aura-bell-backend")
    }
    catch {
        return $false
    }
}

function Test-BackendHealth {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -TimeoutSec 5 -ErrorAction Stop
        return ($response.StatusCode -eq 200)
    }
    catch {
        return $false
    }
}

function Stop-Backend {
    Write-Info "Stopping backend service..."
    try {
        & docker compose -f "$BackendPath\docker-compose.yml" stop backend
        Write-Info "Backend stopped."
    }
    catch {
        Write-Warning "Could not stop backend: $($_.Exception.Message)"
    }
}

function Start-DockerServices {
    param(
        [switch]$ForceRestart
    )
    
    Write-Info "Starting Docker services..."
    
    # Check if Docker is available
    try {
        $null = docker version
    }
    catch {
        Write-Error "Docker is not available. Please install Docker or run services manually."
        return $false
    }
    
    # Check if backend container is already running and healthy
    if (-not $ForceRestart -and (Test-BackendContainer) -and (Test-BackendHealth)) {
        Write-Info "Backend container is already running and healthy. Preserving existing backend."
        return $true
    }
    
    # If ForceRestart, stop the backend first
    if ($ForceRestart -and (Test-BackendContainer)) {
        Write-Info "ForceRestart requested. Stopping existing backend..."
        Stop-Backend
    }
    
    # Start Docker services
    try {
        Write-Info "Starting Docker services..."
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
    param(
        [switch]$ForceRestart
    )
    
    Write-Info "Starting backend service..."
    
    # If the backend container is already running, poll for health
    if (-not $ForceRestart -and (Test-BackendContainer)) {
        Write-Info "Backend container is running. Polling health endpoint..."
        for ($i = 0; $i -lt 30; $i++) {
            if (-not (Test-BackendContainer)) {
                Write-Error "Backend container exited during health polling."
                return $false
            }
            if (Test-BackendHealth) {
                Write-Info "Backend is already running and healthy on port 8000."
                return $true
            }
            Start-Sleep -Seconds 2
        }
        Write-Error "Backend container is running but health check failed after 60 seconds."
        return $false
    }
    
    # Check if port 8000 is occupied by an unrelated process
    if (-not (Test-Port 8000 "Backend")) {
        if (-not (Test-BackendContainer)) {
            Write-Error "Port 8000 is occupied by an unrelated process. Please stop it or use a different port."
            return $false
        }
        if ($ForceRestart) {
            Write-Info "Stopping existing backend..."
            Stop-Backend
        } else {
            Write-Error "Backend is already running on port 8000. Use -ForceRestart to restart."
            return $false
        }
    }
    
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
        
        # Verify backend health
        $healthOk = $false
        for ($i = 0; $i -lt 30; $i++) {
            if (Test-BackendHealth) {
                $healthOk = $true
                break
            }
            Start-Sleep -Seconds 2
        }
        
        if ($healthOk) {
            Write-Info "Backend started successfully and health check passed."
            return $true
        } else {
            Write-Error "Backend started but health check failed after 60 seconds."
            return $false
        }
    }
    catch {
        Write-Error "Failed to start backend: $($_.Exception.Message)"
        return $false
    }
}

function Start-Frontend {
    param(
        [switch]$ForceRestart
    )
    
    Write-Info "Starting frontend service..."
    
    # Check if frontend is already running
    if (-not (Test-Port 3000 "Frontend")) {
        Write-Error "Frontend is already running on port 3000."
        return $false
    }
    
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
        
        # Prepare log paths
        $logsDir = Join-Path $FrontendPath "logs"
        if (-not (Test-Path $logsDir)) {
            New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
        }
        $stdoutLog = Join-Path $logsDir "dev-server-stdout.log"
        $stderrLog = Join-Path $logsDir "dev-server-stderr.log"
        
        # Resolve node.exe from the Node.js installation
        $nodeExe = Join-Path $env:ProgramFiles "nodejs\node.exe"
        if (-not (Test-Path $nodeExe)) {
            throw "node.exe not found at: $nodeExe"
        }
        
        # Resolve the Next.js CLI entry point
        $nextCli = Join-Path $FrontendPath "node_modules\next\dist\bin\next"
        if (-not (Test-Path $nextCli)) {
            throw "Next.js CLI not found at: $nextCli"
        }
        
        $frontendProcess = Start-Process `
            -FilePath $nodeExe `
            -ArgumentList "`"$nextCli`" dev" `
            -WorkingDirectory $FrontendPath `
            -RedirectStandardOutput $stdoutLog `
            -RedirectStandardError $stderrLog `
            -PassThru `
            -NoNewWindow
        
        # Track the process
        $Global:TrackedProcesses["frontend"] = $frontendProcess
        
        # Poll for frontend readiness on port 3000
        Write-Info "Waiting for frontend to become ready on port 3000..."
        $frontendReady = $false
        for ($i = 0; $i -lt 30; $i++) {
            if ($frontendProcess.HasExited) {
                Write-Error "Frontend process exited during startup. Check logs: $stdoutLog, $stderrLog"
                return $false
            }
            if (-not (Test-Port 3000 "Frontend")) {
                $frontendReady = $true
                break
            }
            Start-Sleep -Seconds 2
        }
        
        if ($frontendReady) {
            Write-Info "Frontend started successfully and is listening on port 3000."
            return $true
        } else {
            Write-Error "Frontend failed to start on port 3000 after 60 seconds. Check logs: $stdoutLog, $stderrLog"
            return $false
        }
    }
    catch {
        Write-Error "Failed to start frontend: $($_.Exception.Message)"
        return $false
    }
}

function Stop-AllServices {
    Write-Info "Stopping all AuraBell services..."
    
    # Stop frontend process
    if ($Global:TrackedProcesses.ContainsKey("frontend")) {
        try {
            $proc = $Global:TrackedProcesses["frontend"]
            if (-not $proc.HasExited) {
                $proc.Kill($true)
                $proc.WaitForExit()
                Write-Info "Frontend stopped."
            } else {
                Write-Info "Frontend already exited."
            }
        }
        catch {
            Write-Warning "Could not stop frontend process: $($_.Exception.Message)"
        }
    }
    
    # Stop Docker services
    try {
        Write-Info "Stopping Docker services..."
        & docker compose -f "$BackendPath\docker-compose.yml" down --remove-orphans
        Write-Info "Docker services stopped."
    }
    catch {
        Write-Warning "Could not stop Docker services: $($_.Exception.Message)"
    }
    
    # Clear tracked processes
    $Global:TrackedProcesses.Clear()
    Write-Info "All services stopped successfully."
}

function Restart-AllServices {
    Write-Info "Restarting all AuraBell services..."
    Stop-AllServices
    Start-AllServices
}

function Start-AllServices {
    Write-Info "Starting all AuraBell services..."
    if (Start-DockerServices) {
        $backendResult = Start-Backend
        if (-not $backendResult) {
            Write-Warning "Backend did not start successfully, but continuing with frontend startup."
        }
    } else {
        Write-Warning "Docker services did not start, but continuing with frontend startup."
    }
    $frontendResult = Start-Frontend
    if ($backendResult -and $frontendResult) {
        Write-Info "All services started successfully."
    } elseif (-not $backendResult -and $frontendResult) {
        Write-Info "Frontend started successfully. Backend was already running or skipped."
    } elseif (-not $frontendResult) {
        Write-Warning "Frontend did not start. Check Node.js and port 3000."
    }
}

function Show-Status {
    Write-Info "=== AuraBell Services Status ==="
    
    # Check Docker services
    try {
        Write-Info "Checking Docker services..."
        & docker compose -f "$BackendPath\docker-compose.yml" ps
    }
    catch {
        Write-Warning "Could not check Docker services status: $($_.Exception.Message)"
    }
    
    # Check frontend process
    if ($Global:TrackedProcesses.ContainsKey("frontend")) {
        $frontendProcess = $Global:TrackedProcesses["frontend"]
        if ($frontendProcess -and -not $frontendProcess.HasExited) {
            Write-Info "Frontend: RUNNING (PID: $($frontendProcess.Id))"
        } else {
            Write-Warning "Frontend: STOPPED"
        }
    } else {
        Write-Info "Frontend: NOT STARTED"
    }
    
    # Check ports
    $services = @{
        "Backend" = 8000
        "Frontend" = 3000
        "Database" = 54322
        "Supabase API" = 54321
    }
    
    foreach ($service in $services.GetEnumerator()) {
        $port = $service.Value
        $name = $service.Key
        if (Test-Port $port $name) {
            Write-Info "${name}: PORT $port IS FREE"
        } else {
            Write-Warning "${name}: PORT $port IS IN USE"
        }
    }
    
    # Check environment files
    Write-Info "\n=== Environment Files Status ==="
    $envFile = Join-Path -Path $BackendPath -ChildPath ".env"
    if (Test-Path $envFile) {
        Write-Info ".env: EXISTS"
        $envContent = Get-Content $envFile
        if ($envContent -match "DATABASE_URL") {
            Write-Info "DATABASE_URL: Configured"
        } else {
            Write-Warning "DATABASE_URL: Not configured in .env"
        }
    } else {
        Write-Warning ".env: NOT FOUND (use .env.example for template)"
    }
    
    $envExample = Join-Path -Path $BackendPath -ChildPath ".env.example"
    if (Test-Path $envExample) {
        Write-Info ".env.example: EXISTS (template available)"
    }
    
    Write-Info "\n=== Next Steps ==="
    Write-Info "1. Copy .env.example to .env and configure environment variables"
    Write-Info "2. Run ./scripts/dev-start.ps1 to start services"
    Write-Info "3. Check http://localhost:8000/api/v1/health for backend health"
    Write-Info "4. Check http://localhost:3000 for frontend access"
}

# Main command handling
function Main {
    param(
        [string]$Command = "start"
    )
    
    switch ($Command.ToLower()) {
        "start" {
            Write-Info "Starting AuraBell development environment..."
            if (Start-DockerServices) {
                $backendResult = Start-Backend
                if (-not $backendResult) {
                    Write-Warning "Backend did not start successfully, but continuing with frontend startup."
                }
            } else {
                Write-Warning "Docker services did not start, but continuing with frontend startup."
            }
            $frontendResult = Start-Frontend
            if ($backendResult -and $frontendResult) {
                Write-Info "All services started successfully."
            } elseif (-not $backendResult -and $frontendResult) {
                Write-Info "Frontend started successfully. Backend was already running or skipped."
            } elseif (-not $frontendResult) {
                Write-Warning "Frontend did not start. Check Node.js and port 3000."
            }
        }
        "stop" {
            Stop-AllServices
        }
        "restart" {
            Restart-AllServices
        }
        "status" {
            Show-Status
        }
        default {
            Write-Error "Unknown command: $Command"
            Write-Info "Usage: ./dev-start.ps1 [start|stop|restart|status]"
            exit 1
        }
    }
}

# Execute main function with command line arguments
if ($args.Count -gt 0) {
    $command = $args[0]
    Main -Command $command
} else {
    Main
}
