from app import app, db, User
from werkzeug.security import generate_password_hash

def update_admin_credentials(new_username, new_password):
    with app.app_context():
        # Find the admin user
        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            # Update credentials
            admin.username = new_username
            admin.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
            db.session.commit()
            print(f"Admin credentials updated successfully!")
            print(f"New username: {new_username}")
            print(f"New password: {new_password}")
        else:
            print("No admin user found!")

if __name__ == '__main__':
    # Set your desired admin credentials here
    new_username = input("Enter new admin username: ")
    new_password = input("Enter new admin password: ")
    update_admin_credentials(new_username, new_password) 