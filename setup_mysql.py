import mysql.connector

def setup_mysql_database():
    try:
        # Connect to MySQL server
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conn.cursor()
        
        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS travel_management")
        print("Database 'travel_management' created successfully!")
        
        # Close connection
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error setting up MySQL database: {str(e)}")

if __name__ == "__main__":
    print("Setting up MySQL database...")
    setup_mysql_database()
    print("Setup completed!") 