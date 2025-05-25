# Requires administrator privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "Please run this script as Administrator"
    exit 1
}

$serviceName = "TravelManagementSystem"
$displayName = "Travel Management System"
$description = "Travel Management System Flask Application"
$workingDirectory = $PSScriptRoot
$startupPath = Join-Path $workingDirectory "startup.bat"

# Create a new service using NSSM (Non-Sucking Service Manager)
# First, download NSSM if not present
if (-not (Test-Path "nssm.exe")) {
    Write-Host "Downloading NSSM..."
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $nssmZip = "nssm.zip"
    Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip
    Expand-Archive $nssmZip -DestinationPath "."
    Copy-Item "nssm-2.24\win64\nssm.exe" "nssm.exe"
    Remove-Item $nssmZip -Force
    Remove-Item "nssm-2.24" -Recurse -Force
}

# Remove existing service if it exists
Write-Host "Removing existing service if present..."
.\nssm.exe stop $serviceName 2>$null
.\nssm.exe remove $serviceName confirm 2>$null

# Install the new service
Write-Host "Installing new service..."
.\nssm.exe install $serviceName $startupPath
.\nssm.exe set $serviceName DisplayName $displayName
.\nssm.exe set $serviceName Description $description
.\nssm.exe set $serviceName AppDirectory $workingDirectory
.\nssm.exe set $serviceName AppExit Default Restart
.\nssm.exe set $serviceName AppRestartDelay 10000
.\nssm.exe set $serviceName AppStdout "$workingDirectory\service.log"
.\nssm.exe set $serviceName AppStderr "$workingDirectory\service.log"

# Start the service
Write-Host "Starting service..."
Start-Service $serviceName

# Check service status
$service = Get-Service $serviceName
Write-Host "Service status: $($service.Status)"

if ($service.Status -eq "Running") {
    Write-Host "Service installed and started successfully!"
} else {
    Write-Host "Service installation failed. Please check service.log for details."
} 