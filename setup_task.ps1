# Check for administrator privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Warning "Please run this script as Administrator"
    exit 1
}

$workingDirectory = $PSScriptRoot
$startupPath = Join-Path $workingDirectory "startup.bat"
$trayStartupPath = Join-Path $workingDirectory "tray_startup.bat"

# Remove existing tasks if they exist
Write-Host "Removing existing tasks if present..."
Unregister-ScheduledTask -TaskName "TravelManagementSystem" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "TravelManagementSystemTray" -Confirm:$false -ErrorAction SilentlyContinue

# Create the main application task
$mainAction = New-ScheduledTaskAction -Execute $startupPath -WorkingDirectory $workingDirectory
$mainTrigger = New-ScheduledTaskTrigger -AtLogOn
$mainPrincipal = New-ScheduledTaskPrincipal -UserId (Get-CimInstance -ClassName Win32_ComputerSystem | Select-Object -ExpandProperty UserName) -RunLevel Highest
$mainSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Write-Host "Creating main application task..."
Register-ScheduledTask -TaskName "TravelManagementSystem" `
                      -Action $mainAction `
                      -Trigger $mainTrigger `
                      -Principal $mainPrincipal `
                      -Settings $mainSettings `
                      -Description "Travel Management System Main Application"

# Create the tray application task
$trayAction = New-ScheduledTaskAction -Execute $trayStartupPath -WorkingDirectory $workingDirectory
$trayTrigger = New-ScheduledTaskTrigger -AtLogOn
$trayPrincipal = New-ScheduledTaskPrincipal -UserId (Get-CimInstance -ClassName Win32_ComputerSystem | Select-Object -ExpandProperty UserName) -RunLevel Highest
$traySettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Write-Host "Creating tray application task..."
Register-ScheduledTask -TaskName "TravelManagementSystemTray" `
                      -Action $trayAction `
                      -Trigger $trayTrigger `
                      -Principal $trayPrincipal `
                      -Settings $traySettings `
                      -Description "Travel Management System Tray Application"

# Start the tasks
Write-Host "Starting tasks..."
Start-ScheduledTask -TaskName "TravelManagementSystem"
Start-ScheduledTask -TaskName "TravelManagementSystemTray"

# Check task status
$mainTask = Get-ScheduledTask -TaskName "TravelManagementSystem"
$trayTask = Get-ScheduledTask -TaskName "TravelManagementSystemTray"

Write-Host "Main application task status: $($mainTask.State)"
Write-Host "Tray application task status: $($trayTask.State)"

if ($mainTask.State -eq "Running" -and $trayTask.State -eq "Running") {
    Write-Host "Both tasks created and started successfully!"
} else {
    Write-Host "Task creation completed, but some tasks may not be running. Please check the log files for details."
} 