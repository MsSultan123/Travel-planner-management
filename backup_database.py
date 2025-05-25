import os
import sqlite3
import mysql.connector
from datetime import datetime
import shutil

def backup_sqlite_to_mysql():
    # SQLite connection
    sqlite_conn = sqlite3.connect('travel_management.db')
    sqlite_cursor = sqlite_conn.cursor()
    
    # MySQL connection
    mysql_conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="travel_management"
    )
    mysql_cursor = mysql_conn.cursor()
    
    try:
        # Create database if not exists
        mysql_cursor.execute("CREATE DATABASE IF NOT EXISTS travel_management")
        mysql_conn.database = "travel_management"
        
        # Get all tables from SQLite
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = sqlite_cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            
            # Get table structure
            sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
            columns = sqlite_cursor.fetchall()
            
            # Create table in MySQL
            create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ("
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                if col_type == 'INTEGER':
                    col_type = 'INT'
                elif col_type == 'TEXT':
                    col_type = 'VARCHAR(255)'
                elif col_type == 'REAL':
                    col_type = 'FLOAT'
                create_table_sql += f"{col_name} {col_type}, "
            create_table_sql = create_table_sql.rstrip(', ') + ")"
            
            mysql_cursor.execute(create_table_sql)
            
            # Copy data
            sqlite_cursor.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cursor.fetchall()
            
            if rows:
                placeholders = ', '.join(['%s'] * len(rows[0]))
                insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
                mysql_cursor.executemany(insert_sql, rows)
        
        mysql_conn.commit()
        print("Database backup completed successfully!")
        
    except Exception as e:
        print(f"Error during backup: {str(e)}")
        mysql_conn.rollback()
    
    finally:
        sqlite_cursor.close()
        sqlite_conn.close()
        mysql_cursor.close()
        mysql_conn.close()

def create_backup_file():
    # Create backup directory if it doesn't exist
    backup_dir = "database_backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"travel_management_backup_{timestamp}.sql")
    
    # Use mysqldump from XAMPP
    mysqldump_path = r"C:\xampp\mysql\bin\mysqldump.exe"
    if os.path.exists(mysqldump_path):
        os.system(f'"{mysqldump_path}" -u root travel_management > "{backup_file}"')
        print(f"Backup file created: {backup_file}")
    else:
        print("Error: mysqldump not found in XAMPP directory")

if __name__ == "__main__":
    print("Starting database backup process...")
    backup_sqlite_to_mysql()
    create_backup_file()
    print("Backup process completed!") 