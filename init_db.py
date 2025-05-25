from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def init_database():
    with app.app_context():
        print("Initializing database...")
        
        # Drop all existing tables
        db.drop_all()
        print("Existing tables dropped successfully!")
        
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")
        
        # Create admin user if not exists
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('adminpassword', method='pbkdf2:sha256'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")

if __name__ == "__main__":
    init_database()
    print("Database initialization completed!")