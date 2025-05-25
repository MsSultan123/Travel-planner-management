@echo off
echo Setting up scheduled database backups...

:: Create a scheduled task to run backup_database.py daily at 2 AM
schtasks /create /tn "TravelManagementBackup" /tr "python %~dp0backup_database.py" /sc daily /st 02:00

echo Scheduled task created successfully!
echo The backup will run daily at 2 AM.
echo Backup files will be stored in the database_backups folder.
pause 