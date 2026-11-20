#!/usr/bin/env pwsh
# AuraBell Status Script
# Check the status of all AuraBell services

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendPath = Join-Path -Path $ProjectRoot -ChildPath "backend"
$ComposeFile = Join-Path -Path $BackendPath -ChildPath "docker-compose.yml"

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
        return $false
    }
    catch {
        return $true
    }
}

function Get-ProcessForPort([int]$port) {
    try {
        $netstatOutput = netstat -ano | Out-String
        $netstatLines = $netstatOutput -split "`n"
        foreach ($line in $netstatLines) {
            if ($line -match "LISTENING") {
                $parts = $line -split "\s+"
                $portIndex = -1
                for ($i = 0; $i -lt $parts.Count; $i++) {
                    if ($parts[$i] -eq ":$port") {
                        $portIndex = $i
                        break
                    }
                }
                if ($portIndex -ge 0 -and $portIndex + 1 -lt $parts.Count) {
                    $pid = $parts[$portIndex + 1]
                    if ($pid -and $pid -ne "0") {
                        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
                        if ($proc) {
                            return "$($proc.ProcessName) (PID: $pid)"
                        }
                    }
                }
            }
        }
    }
    catch {
        # Ignore errors
    }
    return $null
}

function Show-DetailedStatus {
    Write-Info "=== AuraBell Services Detailed Status ==="
    
    # Check Docker services
    try {
        Write-Info "Checking Docker services status..."
        if (Test-Path $ComposeFile) {
            try {
                & docker compose -f $ComposeFile ps
            }
            catch {
                Write-Warning "Could not check Docker services status: $($_.Exception.Message)"
            }
        } else {
            Write-Warning "Docker Compose file not found: $ComposeFile"
        }
    }
    catch {
        Write-Warning "Could not check Docker services status: $($_.Exception.Message)"
    }
    
    # Check important ports
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
            $owner = Get-ProcessForPort $port
            if ($owner) {
                Write-Warning "${name}: PORT $port IS IN USE by $owner"
            } else {
                Write-Warning "${name}: PORT $port IS IN USE"
            }
        }
    }
    
    # Check environment files
    Write-Info "`n=== Environment Files Status ==="
    $envFile = Join-Path -Path $BackendPath -ChildPath ".env"
    if (Test-Path $envFile) {
        try {
            $envContent = Get-Content $envFile
            if ($envContent -match "DATABASE_URL") {
                Write-Info ".env: EXISTS, DATABASE_URL: Configured"
            } else {
                Write-Warning ".env: EXISTS, DATABASE_URL: Not configured"
            }
        }
        catch {
            Write-Warning ".env: EXISTS but could not read: $($_.Exception.Message)"
        }
    } else {
        Write-Warning ".env: NOT FOUND (use .env.example for template)"
    }
    
    $envExample = Join-Path -Path $BackendPath -ChildPath ".env.example"
    if (Test-Path $envExample) {
        Write-Info ".env.example: EXISTS (template available)"
    } else {
        Write-Warning ".env.example: NOT FOUND"
    }
    
    Write-Info "`n=== Next Steps ==="
    Write-Info "1. Copy .env.example to .env and configure environment variables"
    Write-Info "2. Run ./scripts/dev-start.ps1 to start services"
    Write-Info "3. Check http://localhost:8000/api/v1/health for backend health"
    Write-Info "4. Check http://localhost:3000 for frontend access"
}

function Main {
    Show-DetailedStatus
}

Main
