from app import db, app
import pymysql
from sqlalchemy_utils import database_exists, create_database # type: ignore

def reset_database():
    try:
        # Configure MySQL connection
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password=''
        )
        
        with connection.cursor() as cursor:
            # Drop database if exists
            cursor.execute('DROP DATABASE IF EXISTS travel_db')
            # Create database
            cursor.execute('CREATE DATABASE travel_db')
            # Use the database
            cursor.execute('USE travel_db')
            
        connection.commit()
        connection.close()
        print("Database reset successful!")
        
        # Create all tables
        with app.app_context():
            db.create_all()
            print("Tables created successfully!")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        
if __name__ == "__main__":
    reset_database()