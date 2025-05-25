import os
import mysql.connector
from datetime import datetime
import glob
import sys

def list_backups():
    """List all available backup files"""
    backup_dir = "database_backups"
    if not os.path.exists(backup_dir):
        print("No backups found - backup directory doesn't exist")
        return []
    
    backups = glob.glob(os.path.join(backup_dir, "travel_management_backup_*.sql"))
    if not backups:
        print("No backup files found")
        return []
    
    print("\nAvailable backups:")
    for i, backup in enumerate(backups, 1):
        filename = os.path.basename(backup)
        # Extract timestamp from filename
        try:
            date_str = filename.split('_')[2:4]  # Get the date and time parts
            date_str = '_'.join(date_str).replace('.sql', '')
            date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
            print(f"{i}. {filename} (Created: {date.strftime('%Y-%m-%d %H:%M:%S')})")
        except:
            print(f"{i}. {filename}")
    
    return backups

def restore_backup(backup_file):
    """Restore the database from a backup file"""
    try:
        # First, recreate the database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conn.cursor()
        
        print("Dropping existing database if exists...")
        cursor.execute("DROP DATABASE IF EXISTS travel_management")
        print("Creating fresh database...")
        cursor.execute("CREATE DATABASE travel_management")
        cursor.close()
        conn.close()
        
        # Now restore from backup using mysql command
        mysql_path = r"C:\xampp\mysql\bin\mysql.exe"
        if os.path.exists(mysql_path):
            restore_command = f'"{mysql_path}" -u root travel_management < "{backup_file}"'
            print("Restoring from backup...")
            result = os.system(restore_command)
            
            if result == 0:
                print("Database restored successfully!")
            else:
                print("Error occurred during restore")
        else:
            print("Error: mysql executable not found in XAMPP directory")
            
    except Exception as e:
        print(f"Error during restore: {str(e)}")

def main():
    backups = list_backups()
    if not backups:
        return
    
    while True:
        try:
            choice = input("\nEnter the number of the backup to restore (or 'q' to quit): ")
            if choice.lower() == 'q':
                return
            
            choice = int(choice)
            if 1 <= choice <= len(backups):
                backup_file = backups[choice - 1]
                confirm = input(f"\nAre you sure you want to restore from {os.path.basename(backup_file)}?\nThis will ERASE all current data! (yes/no): ")
                
                if confirm.lower() == 'yes':
                    restore_backup(backup_file)
                    break
                else:
                    print("Restore cancelled")
                    break
            else:
                print("Invalid choice. Please try again")
        except ValueError:
            print("Please enter a valid number")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("Travel Management System - Database Restore Utility")
    print("=" * 50)
    main() 