# Run as administrator
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {  
    $arguments = "& '" + $myinvocation.mycommand.definition + "'"
    Start-Process powershell -Verb runAs -ArgumentList $arguments
    Break
}

# Get the current directory
$currentDir = Get-Location
$startupScript = Join-Path $currentDir "startup.bat"

# Create the scheduled task
$action = New-ScheduledTaskAction -Execute $startupScript -WorkingDirectory $currentDir
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -RestartInterval (New-TimeSpan -Minutes 1) -RestartCount 3 -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

# Register the task with highest privileges
Register-ScheduledTask -TaskName "TravelManagementSystem" -Action $action -Trigger $trigger -Settings $settings -Description "Starts the Travel Management System automatically" -Force -RunLevel Highest

Write-Host "Automatic startup has been configured successfully!"
Write-Host "The application will start automatically when you log in."
Write-Host "You can check the startup.log file for startup history." 