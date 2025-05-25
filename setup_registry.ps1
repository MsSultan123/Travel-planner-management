# Run as administrator
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {  
    $arguments = "& '" + $myinvocation.mycommand.definition + "'"
    Start-Process powershell -Verb runAs -ArgumentList $arguments
    Break
}

# Get the current directory
$currentDir = Get-Location
$startupScript = Join-Path $currentDir "startup.bat"

# Create a shortcut in the Startup folder
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\TravelManagementSystem.lnk")
$Shortcut.TargetPath = $startupScript
$Shortcut.WorkingDirectory = $currentDir
$Shortcut.Save()

Write-Host "Automatic startup has been configured successfully!"
Write-Host "The application will start automatically when you log in."
Write-Host "You can check the startup.log file for startup history." 