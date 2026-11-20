# AuraBell One-Click Development Launcher

## Overview

The AuraBell One-Click Development Launcher is a comprehensive set of PowerShell scripts and VS Code tasks designed to simplify the development environment setup and management for the AuraBell e-commerce platform. It provides a unified interface to start, stop, restart, and monitor all required development services (backend, frontend, and database) without manually managing multiple terminal commands or Docker sessions.

## What It Does

This launcher automates the entire development environment lifecycle:

- **Environment Validation**: Checks system dependencies and available ports
- **Service Management**: Starts/stops/restarts all AuraBell services
- **Status Monitoring**: Displays real-time status of running services
- **Safety Checks**: Prevents conflicts with existing services
- **Data Protection**: Preserves Docker volumes and database data
- **Error Handling**: Provides clear error messages and recovery guidance

## Required Dependencies

### System Requirements

- **Windows** (PowerShell 5.1 or PowerShell 7+)
- **Docker Desktop** (for Docker-based services)
- **Node.js** (v18+ for frontend)

### Optional Tools

- **Git** (for source management)
- **VS Code** (for integrated tasks)

## Installation and Initial Setup

### 1. Verify Project Location

You should be in the AuraBell project root directory:

```bash
# Navigate to the AuraBell project root
cd D:\navil\TCH\Aura bell

```bash

### 2. Verify Launcher Scripts

The launcher files should be present in the scripts directory:

```powershell
# Check if scripts exist
Get-ChildItem -Path "scripts" -Force

# Expected files:
# - scripts\dev-start.ps1
# - scripts\dev-stop.ps1
# - scripts\dev-status.ps1

```powershell

### 3. Verify VS Code Integration

The `.vscode/tasks.json` file should be present for VS Code task integration:

```powershell
# Check if tasks.json exists
Test-Path "\.vscode\tasks.json"

```powershell

## How to Use the Launcher

### Basic Commands

From the project root directory (`D:\avill\TCH\Aura bell`), run:

#### Start All Services

```powershell
# PowerShell
.\scripts\dev-start.ps1

# Or use VS Code Tasks
Ctrl+Shift+B
Select "AuraBell: Start All"

```powershell

#### Stop All Services

```powershell
# PowerShell
.\scripts\dev-stop.ps1

# Or use VS Code Tasks
Ctrl+Shift+B
Select "AuraBell: Stop All"

```powershell

#### Restart All Services

```powershell
# PowerShell
.\scripts\dev-start.ps1 restart

# Or use VS Code Tasks
Ctrl+Shift+B
Select "AuraBell: Restart"

```powershell

#### Check Service Status

```powershell
# PowerShell
.\scripts\dev-status.ps1

# Or use VS Code Tasks
Ctrl+Shift+B
Select "AuraBell: Status"

```powershell

### VS Code Tasks Integration

The launcher provides four tasks in VS Code:

1. **AuraBell: Start All** - Starts all services
2. **AuraBell: Stop All** - Stops all services
3. **AuraBell: Restart** - Restarts all services
4. **AuraBell: Status** - Shows service status

Access them via `Ctrl+Shift+B` or the Run menu.

## How the Launcher Works

### Service Architecture

The AuraBell project consists of:

- **Backend**: FastAPI service running on port 8000
  - Built with Python 3.11, FastAPI, and uvicorn
  - Uses Supabase PostgreSQL for database
  - Docker containerized for consistent deployment

- **Frontend**: Next.js application running on port 3000
  - Built with Next.js 14.2.15, React, and TypeScript
  - Uses Tailwind CSS for styling
  - Includes authentication and product management features

- **Database**: Supabase PostgreSQL
  - Running locally on port 54322
  - Includes Row Level Security (RLS) for data protection
  - Managed through Supabase CLI

### Service Startup Sequence

1. **Docker Services**: Starts Docker containers (including database)
2. **Backend**: Starts the FastAPI backend service
3. **Frontend**: Starts the Next.js development server

### Service Management Features

- **Port Conflict Detection**: Prevents duplicate service instances
- **Process Tracking**: Manages frontend processes safely
- **Graceful Shutdown**: Preserves data and prevents corruption
- **Health Monitoring**: Provides real-time service status

## Common Issues and Solutions

### Error: Docker is not available

**Solution:** Install Docker Desktop from https://www.docker.com/products/docker-desktop

### Error: Port already in use

**Solution:**
1. Check what's using the port: `netstat -ano | findstr :8000`
2. Stop the conflicting service
3. Or use `-ForceRestart` to stop and restart

### Error: Node.js not found

**Solution:** Install Node.js from https://nodejs.org/

### Error: Permission denied

**Solution:**
1. Run PowerShell as Administrator
2. Or check script execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### Error: Environment file missing

**Solution:**
1. The launcher will automatically copy `.env.example` to `.env`
2. Manual configuration may be needed for database connection details

## Manual Service Management

If the launcher fails, you can run services manually:

### Backend Service

```powershell
# Navigate to backend directory
cd D:\avill\TCH\Aura bell\backend

# Check if .env exists
cp .env.example .env  # edit if needed

# Option 1: Using Docker
docker compose build
docker compose up -d

# Option 2: Directly (if Docker not available)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Health check
curl http://localhost:8000/api/v1/health

```powershell

### Frontend Service

```powershell
# Navigate to frontend directory
cd D:\avill\TCH\Aura bell\frontend

# Install dependencies
npm install

# Start frontend
npm run dev

# Access at http://localhost:3000

```powershell

## Safety Features

### Data Protection

- ✅ **Never deletes Docker volumes**
- ✅ **Preserves database data**
- ✅ **No destructive Docker commands**
- ✅ **Safe shutdown sequence**

### Service Isolation

- ✅ **Only stops services started by launcher**
- ✅ **Port conflict detection**
- ✅ **Duplicate instance prevention**
- ✅ **Process cleanup without collateral damage**

### Configuration Preservation

- ✅ **No automatic .env file modifications**
- ✅ **Maintains existing project configurations**
- ✅ **Production environment protection**
- ✅ **Safe environment variable management**

## Troubleshooting

### Launcher Won't Start

1. Check if Docker is running
2. Verify port availability (8000, 3000, 54322, 54321)
3. Check script execution policy
4. Run with `-Verbose` flag for detailed output

### Partial Service Start

1. Check individual service logs
2. Verify environment variables
3. Manually start services if needed

### Environment Issues

1. Ensure `.env` file is properly configured
2. Check all required dependencies are installed
3. Verify database accessibility

## Integration with Development Workflow

### Daily Development

```powershell
# Morning: Start everything
.\scripts\dev-start.ps1

# During development: Check status periodically
.\scripts\dev-status.ps1

# End of day: Clean shutdown
.\scripts\dev-stop.ps1

```powershell

### CI/CD Integration

The launcher can be integrated into CI/CD pipelines for:

- Automated environment setup
- Service health checks
- Test environment preparation

## Customization

### Adding New Services

To add new services to the launcher:

1. Update `dev-start.ps1` to include service startup logic
2. Update `dev-stop.ps1` to include service shutdown logic
3. Update `dev-status.ps1` to include service status checks
4. Update `.vscode/tasks.json` with new task if needed

### Environment-Specific Configuration

Create environment-specific launcher scripts:

- `scripts/dev-start-dev.ps1` for development
- `scripts/dev-start-prod.ps1` for production
- `scripts/dev-start-ci.ps1` for CI/CD

## Best Practices

1. **Always check status before making changes**
2. **Use `-ForceRestart` only when necessary**
3. **Monitor port conflicts**
4. **Keep `.env` configuration secure**
5. **Regular backups of database data**

## Files Created

- `scripts/dev-start.ps1` - Main launcher script
- `scripts/dev-stop.ps1` - Safe shutdown script
- `scripts/dev-status.ps1` - Status monitoring script
- `.vscode/tasks.json` - VS Code integration
- `docs/DEVELOPMENT_LAUNCHER.md` - This documentation

## Verification

After implementation:

1. ✅ PowerShell scripts are syntactically correct
2. ✅ tasks.json syntax is valid
3. ✅ Status command shows accurate information
4. ✅ Startup process handles errors gracefully
5. ✅ Services start without conflicts
6. ✅ Stop command preserves data and only stops tracked services
7. ✅ Docker volumes and database data remain untouched
8. ✅ Documentation is clear and comprehensive

## Known Limitations

1. **Docker Dependency**: Requires Docker Desktop for Docker-based services
2. **Port Conflicts**: May conflict with existing services on standard ports
3. **Windows-Specific**: Optimized for Windows PowerShell
4. **Manual Supabase Setup**: Requires local Supabase setup for database

## Conclusion

The AuraBell One-Click Development Launcher provides a safe, reliable, and maintainable way to manage the development environment for the AuraBell platform. It follows best practices for service management, data protection, and error handling while maintaining simplicity and ease of use.

For support or issues, please refer to the project documentation or contact the development team.
