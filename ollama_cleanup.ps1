# Self-elevate to admin if needed
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Start-Process powershell.exe "-NoProfile -ExecutionPolicy Bypass -File `"$($MyInvocation.MyCommand.Path)`"" -Verb RunAs
    exit
}

param()

function Reset-OllamaNetwork {
    # Remove port forwarding
    netsh interface portproxy delete v4tov4 listenport=11434 > $null
    
    # Reset Windows Firewall
    Get-NetFirewallRule -DisplayName "Ollama Interceptor*" | Remove-NetFirewallRule
    Get-NetFirewallRule -DisplayName "Ollama Original*" | Remove-NetFirewallRule
    
    # Restore original Ollama firewall rule
    if (-not (Get-NetFirewallRule -DisplayName "Ollama" -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName "Ollama" -Direction Inbound -LocalPort 11434 -Protocol TCP -Action Allow
    }
}

function Stop-ProxyProcesses {
    # Kill proxy processes
    Get-Process ollama_interceptor* -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process python* -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -match "ollama_interceptor"
    } | Stop-Process -Force
}

function Repair-HostsFile {
    $hostsPath = "$env:SystemRoot\System32\drivers\etc\hosts"
    $tempFile = New-TemporaryFile
    
    Get-Content $hostsPath | Where-Object {
        $_ -notmatch "ollama" -and $_ -notmatch "11434" -and $_ -notmatch "11435"
    } | Set-Content $tempFile
    
    Move-Item $tempFile $hostsPath -Force
}

function Test-SystemHealth {
    # Check critical services
    $services = @("WinSock2", "WinRM", "Netman")
    $services | ForEach-Object {
        if ((Get-Service -Name $_).Status -ne "Running") {
            Start-Service -Name $_ -ErrorAction SilentlyContinue
        }
    }
    
    # Reset network stack
    netsh winsock reset > $null
    netsh int ip reset > $null
    ipconfig /flushdns > $null
}

function Invoke-FullCleanup {
    try {
        Write-Host "=== Starting Ollama Environment Reset ===" -ForegroundColor Cyan
        
        Write-Host "Stopping proxy processes..." -ForegroundColor Yellow
        Stop-ProxyProcesses
        
        Write-Host "Resetting network configuration..." -ForegroundColor Yellow
        Reset-OllamaNetwork
        
        Write-Host "Repairing hosts file..." -ForegroundColor Yellow
        Repair-HostsFile
        
        Write-Host "Performing system health check..." -ForegroundColor Yellow
        Test-SystemHealth
        
        Write-Host "=== Cleanup Complete ===" -ForegroundColor Green
        Write-Host "Original network configuration restored"
        Write-Host "All proxy processes terminated"
        Write-Host "System should now use Ollama directly on port 11434"
    }
    catch {
        Write-Host "Error during cleanup: $_" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Execute cleanup
Invoke-FullCleanup
Read-Host "Press Enter to exit" 