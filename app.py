from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta, time
import secrets
from flask_mail import Mail, Message
from dotenv import load_dotenv
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, FileField, SubmitField, SelectField, FloatField
from wtforms.validators import DataRequired, Email, Optional, Length
from werkzeug.utils import secure_filename
import base64
from io import BytesIO
from PIL import Image
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from functools import wraps
from popular_destinations import popular_destinations
from config import Config
import mysql.connector
from mysql.connector import Error
import traceback
import random

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# MySQL Configuration
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',  # or your XAMPP MySQL password
        database='travel_management'
    )

# Initialize security extensions
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["500 per day", "100 per hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)

talisman = Talisman(
    app,
    force_https=False,
    strict_transport_security=True,
    session_cookie_secure=True,
    content_security_policy={
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline' 'unsafe-eval'",
        'style-src': "'self' 'unsafe-inline'",
        'img-src': "'self' data:",
        'font-src': "'self'",
        'connect-src': "'self'"
    },
    feature_policy={
        'geolocation': "'none'",
        'camera': "'none'",
        'microphone': "'none'",
        'payment': "'none'",
        'usb': "'none'"
    }
)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Initialize mail
mail = Mail(app)

# Security configurations
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['SECRET_KEY'] = 'your-very-secret-key'

# Email Configuration
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Configure upload folders
UPLOAD_FOLDER = 'static/uploads/profile_pictures'
PAYMENT_PROOF_FOLDER = 'static/uploads/payment_proofs'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PAYMENT_PROOF_FOLDER'] = PAYMENT_PROOF_FOLDER

# Create upload folders if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PAYMENT_PROOF_FOLDER, exist_ok=True)

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data.get('id')) if user_data.get('id') else None
        self.username = user_data.get('username')
        self.email = user_data.get('email')
        self.password_hash = user_data.get('password_hash')
        self.first_name = user_data.get('first_name')
        self.last_name = user_data.get('last_name')
        self.is_admin = int(user_data.get('is_admin', 0))  # Ensure int for MySQL
        self.status = user_data.get('status', 'active')
        self.profile_picture = user_data.get('profile_picture')
        self.phone_number = user_data.get('phone_number')
        self.location = user_data.get('location')
        self.date_of_birth = user_data.get('date_of_birth')
        self.created_at = user_data.get('created_at', datetime.utcnow())
        self.reset_token = user_data.get('reset_token')
        self.reset_token_expires = user_data.get('reset_token_expires')

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        return User(user_data) if user_data else None

    @staticmethod
    def get_by_username(username):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        return User(user_data) if user_data else None

    @staticmethod
    def get_by_email(email):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        return User(user_data) if user_data else None

    def save(self):
        conn = get_db_connection()
        cursor = conn.cursor()
        user_data = {
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_admin': int(self.is_admin),
            'status': self.status,
            'profile_picture': self.profile_picture,
            'phone_number': self.phone_number,
            'location': self.location,
            'date_of_birth': self.date_of_birth,
            'created_at': self.created_at,
            'reset_token': self.reset_token,
            'reset_token_expires': self.reset_token_expires
        }
        if self.id:
            # Update existing user
            query = """UPDATE users SET \
                username = %s, email = %s, password_hash = %s, first_name = %s,\
                last_name = %s, is_admin = %s, status = %s, profile_picture = %s,\
                phone_number = %s, location = %s, date_of_birth = %s,\
                created_at = %s, reset_token = %s, reset_token_expires = %s\
                WHERE id = %s"""
            values = (
                user_data['username'], user_data['email'], user_data['password_hash'],
                user_data['first_name'], user_data['last_name'], user_data['is_admin'],
                user_data['status'], user_data['profile_picture'], user_data['phone_number'],
                user_data['location'], user_data['date_of_birth'], user_data['created_at'],
                user_data['reset_token'], user_data['reset_token_expires'], self.id
            )
            cursor.execute(query, values)
        else:
            # Insert new user
            query = """INSERT INTO users (\
                username, email, password_hash, first_name, last_name, is_admin,\
                status, profile_picture, phone_number, location, date_of_birth,\
                created_at, reset_token, reset_token_expires\
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            values = (
                user_data['username'], user_data['email'], user_data['password_hash'],
                user_data['first_name'], user_data['last_name'], user_data['is_admin'],
                user_data['status'], user_data['profile_picture'], user_data['phone_number'],
                user_data['location'], user_data['date_of_birth'], user_data['created_at'],
                user_data['reset_token'], user_data['reset_token_expires']
            )
            cursor.execute(query, values)
            self.id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Additional security headers
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'"
    return response

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# Routes
@app.route('/')
def index():
    return render_template('index.html', popular_destinations=popular_destinations)

@app.route('/destinations')
def destinations():
    return render_template('destinations.html', destinations=popular_destinations)

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("20 per minute")
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))
            
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return render_template('login.html')
            
        user = User.get_by_username(username)
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            
            # Create notification using MySQL
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO notifications (user_id, message, type, is_read, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                user.id,
                'Login successful',
                'login',
                False,
                datetime.utcnow()
            ))
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Login successful!', 'success')
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        is_admin = 1 if request.form.get('is_admin', '0') == '1' else 0
        if not all([username, email, password, first_name, last_name]):
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))
        if User.get_by_username(username):
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        if User.get_by_email(email):
            flash('Email already exists', 'error')
            return redirect(url_for('register'))
        try:
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            user = User({
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'first_name': first_name,
                'last_name': last_name,
                'is_admin': is_admin,
                'status': 'active',
                'created_at': datetime.utcnow()
            })
            user.save()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            traceback.print_exc()
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM trips WHERE user_id = %s", (current_user.id,))
    trips = cursor.fetchall()
    now = datetime.now().date()
    for trip in trips:
        trip['is_upcoming'] = trip['start_date'] > now
    cursor.close()
    conn.close()
    return render_template('dashboard.html', 
                         trips=trips, 
                         now=now,
                         timedelta=timedelta)

@app.route('/logout')
@login_required
def logout():
    # Create logout notification using MySQL
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO notifications (user_id, message, type, is_read, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        current_user.id,
        'Logout successful',
        'logout',
        False,
        datetime.utcnow()
    ))
    conn.commit()
    cursor.close()
    conn.close()
    logout_user()
    return render_template('logout_message.html')

@app.route('/add_trip', methods=['GET', 'POST'])
@login_required
def add_trip():
    domestic_special = ['Dhaka', 'Khulna', 'Barishal', 'Noakhali', 'Sundarban']
    international_special = ['Eiffel Tower']

    if request.method == 'POST':
        destination = request.form.get('to_location')
        tour_type = request.form.get('tour_type')
        num_persons = int(request.form.get('num_persons', 1))
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d').date()
        start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d').date()
        description = request.form.get('description', '')

        # Calculate amount
        if destination in domestic_special:
            amount = 5000
            if tour_type == 'Family Tour':
                amount += 5000
            if tour_type == 'Long Tour':
                amount += 3000
        elif destination in international_special:
            amount = 500000
        elif destination in ['Dhaka', 'Foridpur', 'Gazipur', 'Gopalganj', 'Kishorganj', 'Cox\'s Bazar', 'Bandarban', 'Sundarbans']:
            amount = random.randint(5000, 10000)
        else:
            # International
            amount = random.randint(100000, 1500000)

        # Create trip record
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO trips (
                user_id, destination, start_date, start_time, end_date,
                description, status, tour_type, amount, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            current_user.id, destination, start_date, start_time, end_date,
            description, 'active', tour_type, amount, datetime.utcnow()
        ))
        
        trip_id = cursor.lastrowid

        # Create notification
        cursor.execute("""
            INSERT INTO notifications (user_id, trip_id, message, type, is_read, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            current_user.id, trip_id,
            f'New trip created to {destination}',
            'trip_created',
            0,  # Using 0 instead of False for MySQL
            datetime.utcnow()
        ))

        conn.commit()
        cursor.close()
        conn.close()

        flash('Trip created successfully!', 'success')
        return redirect(url_for('dashboard'))

    # GET request - show the form
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT district FROM district_tour_prices")
    destinations = [row['district'] for row in cursor.fetchall()]
    cursor.close()
    conn.close()

    # Default amount for GET (can be 5000 or blank)
    amount = 5000
    return render_template('add_trip.html', destinations=destinations, amount=amount)

@app.route('/cancel_trip/<int:trip_id>', methods=['POST'])
@login_required
def cancel_trip(trip_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get trip details
    cursor.execute("SELECT * FROM trips WHERE id = %s", (trip_id,))
    trip = cursor.fetchone()
    
    if not trip:
        flash('Trip not found', 'error')
        return redirect(url_for('dashboard'))
    
    # Check if the trip belongs to the current user
    if trip['user_id'] != current_user.id:
        flash('You are not authorized to cancel this trip', 'error')
        return redirect(url_for('dashboard'))
    
    # Check if the trip is already cancelled
    if trip['status'] == 'cancelled':
        flash('This trip is already cancelled', 'error')
        return redirect(url_for('dashboard'))
    
    # Check if the trip has already started
    if trip['start_date'] <= datetime.now().date():
        flash('Cannot cancel a trip that has already started', 'error')
        return redirect(url_for('dashboard'))
    
    # Update trip status
    cursor.execute("UPDATE trips SET status = 'cancelled' WHERE id = %s", (trip_id,))
    
    # Create notification
    cursor.execute("""
        INSERT INTO notifications (user_id, trip_id, message, type, is_read, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        current_user.id, trip_id,
        f'Trip cancelled (Trip ID: {trip_id}, {trip["destination"]}, {trip["start_date"]} to {trip["end_date"]})',
        'trip_cancel', False, datetime.utcnow()
    ))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Trip cancelled successfully', 'success')
    return redirect(url_for('dashboard'))

@app.route('/forgot_password', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def forgot_password():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        user = User.get_by_email(identifier) or User.get_by_username(identifier)
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
            user.save()
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message('Password Reset Request', recipients=[user.email])
            msg.body = f"To reset your password, visit the following link:\n{reset_url}\n\nThis link will expire in 1 hour."
            mail.send(msg)
            flash('An email has been sent with instructions to reset your password.', 'info')
            return redirect(url_for('login'))
        else:
            flash('No account found with that email address or mobile number.', 'error')
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def reset_password(token):
    user = User.get_by_username(token)
    if not user or user.reset_token_expires < datetime.utcnow():
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('reset_password', token=token))
        user.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        user.reset_token = None
        user.reset_token_expires = None
        user.save()
        flash('Your password has been reset successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', token=token)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
@limiter.limit("5 per hour")
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not check_password_hash(current_user.password_hash, current_password):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('change_password'))

        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return redirect(url_for('change_password'))

        current_user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        current_user.save()
        flash('Your password has been changed successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('change_password.html')

@app.route('/take_some_idea')
def take_some_idea():
    return render_template('take_some_idea.html')

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[Optional(), Length(max=50)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=50)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    phone_number = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    location = StringField('Location', validators=[Optional(), Length(max=100)])
    profile_picture = FileField('Profile Picture')
    submit = SubmitField('Update Profile')

class PaymentForm(FlaskForm):
    payment_method = SelectField('Payment Method', choices=[
        ('bKash', 'bKash'),
        ('Nagad', 'Nagad'),
        ('Rocket', 'Rocket'),
        ('credit_card', 'Credit Card'),
        ('mastercard', 'MasterCard'),
        ('bank_transfer', 'Bank Transfer')
    ], validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    transaction_id = StringField('Transaction ID', validators=[Optional()])
    proof_file = FileField('Payment Proof (Image or PDF)', validators=[Optional()])
    submit = SubmitField('Make Payment')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, folder, prefix=''):
    """Securely save an uploaded file with error handling"""
    try:
        if file and allowed_file(file.filename):
            # Generate secure filename
            filename = secure_filename(f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
            file_path = os.path.join(folder, filename)
            
            # Ensure directory exists
            os.makedirs(folder, exist_ok=True)
            
            # Save file
            file.save(file_path)
            
            # For images, verify and optimize
            if file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                try:
                    with Image.open(file_path) as img:
                        # Verify it's a valid image
                        img.verify()
                        
                        # Reopen and optimize
                        img = Image.open(file_path)
                        if img.mode in ('RGBA', 'LA'):
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            background.paste(img, mask=img.split()[-1])
                            img = background
                        img = img.convert('RGB')
                        img.save(file_path, 'JPEG', quality=85, optimize=True)
                except Exception as e:
                    print(f"Error processing image: {e}")
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    raise ValueError("Invalid image file")
            
            return os.path.join(os.path.basename(folder), filename)
        else:
            raise ValueError("Invalid file type")
    except Exception as e:
        print(f"Error saving file: {e}")
        raise

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        try:
            # Update basic profile information
            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data
            current_user.date_of_birth = form.date_of_birth.data
            current_user.phone_number = form.phone_number.data
            current_user.location = form.location.data

            # Handle profile picture upload
            if form.profile_picture.data:
                try:
                    # Delete old profile picture if exists and is not default
                    if current_user.profile_picture and current_user.profile_picture != 'uploads/profile_pictures/default.jpg':
                        old_file_path = os.path.join('static', current_user.profile_picture)
                        if os.path.exists(old_file_path):
                            os.remove(old_file_path)
                    
                    # Save new profile picture
                    relative_path = save_file(
                        form.profile_picture.data,
                        app.config['UPLOAD_FOLDER'],
                        prefix=str(current_user.id)
                    )
                    current_user.profile_picture = relative_path
                    
                except ValueError as e:
                    flash(str(e), 'error')
                    return redirect(url_for('profile'))
                except Exception as e:
                    flash('Error processing profile picture. Please try again.', 'error')
                    return redirect(url_for('profile'))

            current_user.save()
            flash('Your profile has been updated!', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            flash('An error occurred while updating your profile. Please try again.', 'error')
            return redirect(url_for('profile'))

    # Pre-populate form with existing data
    form.first_name.data = current_user.first_name
    form.last_name.data = current_user.last_name
    form.date_of_birth.data = current_user.date_of_birth
    form.phone_number.data = current_user.phone_number
    form.location.data = current_user.location

    # Set default profile picture if none exists
    if not current_user.profile_picture:
        current_user.profile_picture = 'uploads/profile_pictures/default.jpg'
        current_user.save()

    return render_template('profile.html', form=form)

@app.route('/trip/<int:trip_id>/payment', methods=['GET', 'POST'])
@login_required
def make_payment(trip_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM trips WHERE id = %s", (trip_id,))
    trip = cursor.fetchone()
    if not trip:
        cursor.close()
        conn.close()
        flash('Trip not found.', 'error')
        return redirect(url_for('dashboard'))
    if trip['user_id'] != current_user.id:
        cursor.close()
        conn.close()
        flash('You are not authorized to make payments for this trip.', 'error')
        return redirect(url_for('dashboard'))
    # Check if trip is already paid
    cursor.execute("SELECT * FROM payments WHERE trip_id = %s AND status = 'completed'", (trip_id,))
    existing_payment = cursor.fetchone()
    if existing_payment:
        cursor.close()
        conn.close()
        flash('This trip has already been paid for.', 'info')
        return redirect(url_for('dashboard'))
    form = PaymentForm()
    if form.validate_on_submit():
        try:
            proof_file_path = None
            if form.proof_file.data:
                try:
                    proof_file_path = save_file(
                        form.proof_file.data,
                        app.config['PAYMENT_PROOF_FOLDER'],
                        prefix=f"payment_{trip_id}_{current_user.id}"
                    )
                except ValueError as e:
                    flash(str(e), 'error')
                    return redirect(request.url)
                except Exception as e:
                    flash('Error processing payment proof. Please try again.', 'error')
                    return redirect(request.url)
            # Validate payment amount
            if form.amount.data <= 0:
                flash('Payment amount must be greater than zero.', 'error')
                return redirect(request.url)
            # Create payment record
            cursor.execute("""
                INSERT INTO payments (trip_id, amount, payment_method, transaction_id, status, proof_file)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                trip_id, form.amount.data, form.payment_method.data, form.transaction_id.data, 'pending', proof_file_path
            ))
            payment_id = cursor.lastrowid
            # Create notification for admin
            cursor.execute("SELECT id FROM users WHERE is_admin = TRUE")
            admins = cursor.fetchall()
            for admin in admins:
                cursor.execute("""
                    INSERT INTO notifications (user_id, trip_id, message, type, is_read, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    admin['id'], trip_id,
                    f'New payment pending for trip {trip_id} by {current_user.username}',
                    'payment_pending', False, datetime.utcnow()
                ))
            # Create notification for user
            cursor.execute("""
                INSERT INTO notifications (user_id, trip_id, message, type, is_read, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                current_user.id, trip_id,
                f'Payment initiated for trip to {trip["destination"]}. Amount: {form.amount.data}',
                'payment_initiated', False, datetime.utcnow()
            ))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Payment has been initiated. Please wait for admin verification.', 'info')
            return redirect(url_for('payment_status', payment_id=payment_id))
        except Exception as e:
            cursor.close()
            conn.close()
            flash('An error occurred while processing your payment. Please try again.', 'error')
            return redirect(request.url)
    cursor.close()
    conn.close()
    return render_template('payment.html', form=form, trip=trip)

@app.route('/payment/<int:payment_id>/status')
@login_required
def payment_status(payment_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM payments WHERE id = %s", (payment_id,))
    payment = cursor.fetchone()
    if not payment:
        cursor.close()
        conn.close()
        flash('Payment not found.', 'error')
        return redirect(url_for('dashboard'))
    # Get trip for user check
    cursor.execute("SELECT * FROM trips WHERE id = %s", (payment['trip_id'],))
    trip = cursor.fetchone()
    if not trip or trip['user_id'] != current_user.id:
        cursor.close()
        conn.close()
        flash('You are not authorized to view this payment.', 'error')
        return redirect(url_for('dashboard'))
    # Get payment history
    cursor.execute("""
        SELECT * FROM payments 
        WHERE trip_id = %s 
        ORDER BY created_at DESC 
        LIMIT 10
    """, (payment['trip_id'],))
    payment_history = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('payment_status.html', payment=payment, payment_history=payment_history)

@app.route('/trip/<int:trip_id>/payments')
@login_required
def trip_payments(trip_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM trips WHERE id = %s", (trip_id,))
    trip = cursor.fetchone()
    if not trip or trip['user_id'] != current_user.id:
        cursor.close()
        conn.close()
        flash('You are not authorized to view payments for this trip.', 'error')
        return redirect(url_for('dashboard'))
    cursor.execute("SELECT * FROM payments WHERE trip_id = %s", (trip_id,))
    payments = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('trip_payments.html', trip=trip, payments=payments)

@app.route('/payment/<int:payment_id>/print')
@login_required
def print_receipt(payment_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM payments WHERE id = %s", (payment_id,))
    payment = cursor.fetchone()
    if not payment:
        cursor.close()
        conn.close()
        flash('Payment not found.', 'error')
        return redirect(url_for('dashboard'))
    cursor.execute("SELECT * FROM trips WHERE id = %s", (payment['trip_id'],))
    trip = cursor.fetchone()
    if not trip or trip['user_id'] != current_user.id:
        cursor.close()
        conn.close()
        flash('You are not authorized to view this payment.', 'error')
        return redirect(url_for('dashboard'))
    cursor.close()
    conn.close()
    return render_template('print_receipt.html', payment=payment, trip=trip)

@app.route('/notifications')
@login_required
def notifications():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM notifications 
        WHERE user_id = %s 
        ORDER BY created_at DESC 
        LIMIT 10
    """, (current_user.id,))
    notifications = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('notifications.html', notifications=notifications)

@app.route('/notifications/mark_read/<int:notification_id>')
@login_required
def mark_notification_read(notification_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get notification
    cursor.execute("SELECT * FROM notifications WHERE id = %s", (notification_id,))
    notification = cursor.fetchone()
    
    if not notification:
        flash('Notification not found', 'error')
        return redirect(url_for('notifications'))
    
    if notification['user_id'] != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('notifications'))
    
    # Update notification
    cursor.execute("UPDATE notifications SET is_read = TRUE WHERE id = %s", (notification_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for('notifications'))

@app.route('/trip/<int:trip_id>/check_in', methods=['POST'])
@login_required
def trip_check_in(trip_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM trips WHERE id = %s", (trip_id,))
    trip = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if trip['user_id'] != current_user.id:
        flash('Unauthorized access.', 'error')
        return redirect(url_for('dashboard'))
    
    now = datetime.now()
    trip_start = datetime.combine(trip['start_date'], trip['start_time'])
    
    # Allow check-in within 1 hour before start time
    if now < trip_start - timedelta(hours=1):
        flash('Too early to check in. You can check in 1 hour before the start time.', 'error')
        return redirect(url_for('dashboard'))
    
    if trip['is_missed']:
        flash('Trip has been marked as missed. Cannot check in now.', 'error')
        return redirect(url_for('dashboard'))
    
    cursor = conn.cursor()
    cursor.execute("UPDATE trips SET check_in_time = %s WHERE id = %s", (now, trip_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    flash('Successfully checked in for the trip!', 'success')
    return redirect(url_for('dashboard'))

def check_missed_trips():
    """Background task to check for missed trips and create notifications"""
    with app.app_context():
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM trips WHERE status = 'active' AND check_in_time IS NULL")
            trips = cursor.fetchall()
            
            for trip in trips:
                try:
                    if trip['is_missed'] and trip['status'] != 'missed':
                        cursor.execute("UPDATE trips SET status = 'missed' WHERE id = %s", (trip['id'],))
                        notification = {
                            'user_id': trip['user_id'],
                            'trip_id': trip['id'],
                            'message': f'You missed your trip to {trip["destination"]} scheduled for {trip["start_date"]} at {trip["start_time"]}.',
                            'type': 'trip_missed',
                            'created_at': datetime.utcnow()
                        }
                        cursor.execute("""
                            INSERT INTO notifications (user_id, trip_id, message, type, created_at)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (
                            trip['user_id'], trip['id'],
                            notification['message'], notification['type'], notification['created_at']
                        ))
                        conn.commit()
                except Exception as e:
                    print(f"Error processing trip {trip['id']}: {str(e)}")
                    continue
            
        except Exception as e:
            print(f"Error in check_missed_trips: {str(e)}")

def send_trip_reminders():
    """Background task to send trip reminders"""
    with app.app_context():
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM trips WHERE status = 'active' AND start_date >= CURDATE()")
            trips = cursor.fetchall()
            
            for trip in trips:
                try:
                    trip_start = datetime.combine(trip['start_date'], trip['start_time'])
                    time_until = trip_start - datetime.now()
                    if time_until:
                        # Send reminder 24 hours before
                        if timedelta(hours=23) <= time_until <= timedelta(hours=24):
                            notification = {
                                'user_id': trip['user_id'],
                                'trip_id': trip['id'],
                                'message': f'Reminder: Your trip to {trip["destination"]} starts tomorrow at {trip["start_time"]}!',
                                'type': 'trip_reminder',
                                'created_at': datetime.utcnow()
                            }
                            cursor.execute("""
                                INSERT INTO notifications (user_id, trip_id, message, type, created_at)
                                VALUES (%s, %s, %s, %s, %s)
                            """, (
                                trip['user_id'], trip['id'],
                                notification['message'], notification['type'], notification['created_at']
                            ))
                            conn.commit()
                        # Send reminder 1 hour before
                        elif timedelta(minutes=55) <= time_until <= timedelta(hours=1):
                            notification = {
                                'user_id': trip['user_id'],
                                'trip_id': trip['id'],
                                'message': f'Reminder: Your trip to {trip["destination"]} starts in 1 hour at {trip["start_time"]}!',
                                'type': 'trip_reminder',
                                'created_at': datetime.utcnow()
                            }
                            cursor.execute("""
                                INSERT INTO notifications (user_id, trip_id, message, type, created_at)
                                VALUES (%s, %s, %s, %s, %s)
                            """, (
                                trip['user_id'], trip['id'],
                                notification['message'], notification['type'], notification['created_at']
                            ))
                            conn.commit()
                except Exception as e:
                    print(f"Error processing trip {trip['id']}: {str(e)}")
                    continue
            
        except Exception as e:
            print(f"Error in send_trip_reminders: {str(e)}")

# Add background tasks
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_missed_trips, trigger="interval", minutes=5)
scheduler.add_job(func=send_trip_reminders, trigger="interval", minutes=5)
scheduler.start()

@app.route('/register_face', methods=['POST'])
@login_required
def register_face():
    try:
        face_image_data = request.form.get('face_image')
        if not face_image_data:
            flash('No face image provided', 'error')
            return redirect(url_for('profile'))
        # Convert base64 image to file
        image_data = base64.b64decode(face_image_data.split(',')[1])
        image = Image.open(BytesIO(image_data))
        # Save the image
        filename = f"{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)
        # Update user's profile picture
        relative_path = os.path.join('uploads/profile_pictures', filename)
        current_user.profile_picture = relative_path
        current_user.save()
        # Create notification using MySQL
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO notifications (user_id, message, type, is_read, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            current_user.id, 'Face registered successfully', 'face_registration', False, datetime.utcnow()
        ))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Face registered successfully!', 'success')
        return redirect(url_for('profile'))
    except Exception as e:
        flash('Error registering face. Please try again.', 'error')
        return redirect(url_for('profile'))

@app.route('/update_status_face', methods=['POST'])
@login_required
def update_status_face():
    try:
        face_image_data = request.form.get('face_image')
        if not face_image_data:
            flash('No face image provided', 'error')
            return redirect(url_for('profile'))
        # Toggle status
        current_user.status = 'active' if current_user.status == 'deactive' else 'deactive'
        current_user.save()
        # Create notification using MySQL
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO notifications (user_id, message, type, is_read, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            current_user.id, f'Status updated to {current_user.status}', 'status_update', False, datetime.utcnow()
        ))
        conn.commit()
        cursor.close()
        conn.close()
        flash(f'Status updated to {current_user.status}!', 'success')
        return redirect(url_for('profile'))
    except Exception as e:
        flash('Error updating status. Please try again.', 'error')
        return redirect(url_for('profile'))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Admin Routes
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get counts for dashboard
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM trips")
    total_trips = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM payments")
    total_payments = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM payments WHERE status = 'pending'")
    pending_payments = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM trips WHERE status = 'active'")
    active_trips = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM trips WHERE status = 'cancelled'")
    cancelled_trips = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM support_requests WHERE status = 'open'")
    open_support_requests = cursor.fetchone()['count']
    
    # Get recent activities
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 5")
    recent_users = cursor.fetchall()
    
    cursor.execute("SELECT * FROM trips ORDER BY created_at DESC LIMIT 5")
    recent_trips = cursor.fetchall()
    for trip in recent_trips:
        cursor.execute("SELECT username FROM users WHERE id = %s", (trip['user_id'],))
        user = cursor.fetchone()
        trip['user'] = user if user else {'username': 'Unknown'}
    
    cursor.execute("SELECT * FROM payments ORDER BY created_at DESC LIMIT 5")
    recent_payments = cursor.fetchall()
    
    cursor.execute("SELECT * FROM support_requests ORDER BY created_at DESC LIMIT 5")
    recent_support_requests = cursor.fetchall()
    for req in recent_support_requests:
        cursor.execute("SELECT username FROM users WHERE id = %s", (req['user_id'],))
        user = cursor.fetchone()
        req['user'] = user if user else {'username': 'Unknown'}
    
    cursor.close()
    conn.close()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_trips=total_trips,
                         total_payments=total_payments,
                         pending_payments=pending_payments,
                         active_trips=active_trips,
                         cancelled_trips=cancelled_trips,
                         open_support_requests=open_support_requests,
                         recent_users=recent_users,
                         recent_trips=recent_trips,
                         recent_payments=recent_payments,
                         recent_support_requests=recent_support_requests)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if search_query:
        cursor.execute("""
            SELECT * FROM users 
            WHERE username LIKE %s 
            OR email LIKE %s 
            OR first_name LIKE %s 
            OR last_name LIKE %s 
            OR phone_number LIKE %s 
            OR location LIKE %s
            LIMIT 10 OFFSET %s
        """, (
            f'%{search_query}%', f'%{search_query}%', f'%{search_query}%',
            f'%{search_query}%', f'%{search_query}%', f'%{search_query}%',
            (page - 1) * 10
        ))
    else:
        cursor.execute("SELECT * FROM users LIMIT 10 OFFSET %s", ((page - 1) * 10,))
    
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('admin/users.html', users=users, search_query=search_query)

@app.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('admin_users'))
    
    if request.method == 'POST':
        try:
            cursor.execute("""
                UPDATE users SET 
                username = %s, email = %s, first_name = %s, last_name = %s,
                phone_number = %s, location = %s, status = %s, is_admin = %s
                WHERE id = %s
            """, (
                request.form.get('username'),
                request.form.get('email'),
                request.form.get('first_name'),
                request.form.get('last_name'),
                request.form.get('phone_number'),
                request.form.get('location'),
                request.form.get('status'),
                request.form.get('is_admin') == 'on',
                user_id
            ))
            
            new_password = request.form.get('new_password')
            if new_password:
                cursor.execute("""
                    UPDATE users SET password_hash = %s WHERE id = %s
                """, (generate_password_hash(new_password), user_id))
            
            conn.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('admin_users'))
            
        except Exception as e:
            flash('Error updating user: ' + str(e), 'error')
    
    cursor.close()
    conn.close()
    
    return render_template('admin/edit_user.html', user=user)

@app.route('/admin/payments')
@login_required
@admin_required
def admin_payments():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if status:
        cursor.execute("""
            SELECT * FROM payments 
            WHERE status = %s 
            LIMIT 10 OFFSET %s
        """, (status, (page - 1) * 10))
    else:
        cursor.execute("SELECT * FROM payments LIMIT 10 OFFSET %s", ((page - 1) * 10,))
    
    payments = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('admin/payments.html', payments=payments, status=status)

@app.route('/admin/payment/<int:payment_id>/update', methods=['POST'])
@login_required
@admin_required
def admin_update_payment(payment_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM payments WHERE id = %s", (payment_id,))
    payment = cursor.fetchone()
    
    if not payment:
        flash('Payment not found', 'error')
        return redirect(url_for('admin_payments'))
    
    new_status = request.form.get('status')
    
    if new_status in ['pending', 'completed', 'failed']:
        if payment['status'] != new_status:
            cursor.execute("""
                UPDATE payments SET status = %s WHERE id = %s
            """, (new_status, payment_id))
            # Update trip status based on payment status
            if new_status == 'completed':
                cursor.execute("UPDATE trips SET status = 'paid' WHERE id = %s", (payment['trip_id'],))
            else:
                cursor.execute("UPDATE trips SET status = 'pending' WHERE id = %s", (payment['trip_id'],))
            # Create notification for the user
            cursor.execute("""
                INSERT INTO notifications (user_id, trip_id, message, type, is_read, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                payment['trip_id'],
                payment['trip_id'],
                f'Payment status updated to {new_status}',
                'payment_status',
                False,
                datetime.utcnow()
            ))
            conn.commit()
            flash(f'Payment status updated to {new_status}', 'success')
        else:
            flash('Payment status is already set to that value', 'info')
    else:
        flash('Invalid payment status', 'error')
    
    cursor.close()
    conn.close()
    
    return redirect(url_for('admin_payments'))

@app.route('/admin/trips')
@login_required
@admin_required
def admin_trips():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if status:
        cursor.execute("""
            SELECT * FROM trips 
            WHERE status = %s 
            LIMIT 10 OFFSET %s
        """, (status, (page - 1) * 10))
    else:
        cursor.execute("SELECT * FROM trips LIMIT 10 OFFSET %s", ((page - 1) * 10,))
    
    trips = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('admin/trips.html', trips=trips, status=status)

@app.route('/admin/trip/<int:trip_id>/update', methods=['POST'])
@login_required
@admin_required
def admin_update_trip(trip_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM trips WHERE id = %s", (trip_id,))
    trip = cursor.fetchone()
    
    if not trip:
        flash('Trip not found', 'error')
        return redirect(url_for('admin_trips'))
    
    action = request.form.get('action')
    
    if action == 'cancel':
        if trip['status'] != 'cancelled':
            cursor.execute("""
                UPDATE trips SET status = 'cancelled' WHERE id = %s
            """, (trip_id,))
            
            # Create notification for the user
            cursor.execute("""
                INSERT INTO notifications (user_id, trip_id, message, type, is_read, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                trip['user_id'],
                trip_id,
                'Your trip has been cancelled by admin',
                'trip_cancelled',
                False,
                datetime.utcnow()
            ))
            
            conn.commit()
            flash('Trip cancelled successfully', 'success')
        else:
            flash('Trip is already cancelled', 'info')
    elif action == 'activate':
        if trip['status'] != 'active':
            cursor.execute("""
                UPDATE trips SET status = 'active' WHERE id = %s
            """, (trip_id,))
            
            # Create notification for the user
            cursor.execute("""
                INSERT INTO notifications (user_id, trip_id, message, type, is_read, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                trip['user_id'],
                trip_id,
                'Your trip has been activated by admin',
                'trip_activated',
                False,
                datetime.utcnow()
            ))
            
            conn.commit()
            flash('Trip activated successfully', 'success')
        else:
            flash('Trip is already active', 'info')
    
    cursor.close()
    conn.close()
    
    return redirect(url_for('admin_trips'))

@app.route('/admin/support')
@login_required
@admin_required
def admin_support():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if status:
        cursor.execute("""
            SELECT * FROM support_requests 
            WHERE status = %s 
            LIMIT 10 OFFSET %s
        """, (status, (page - 1) * 10))
    else:
        cursor.execute("SELECT * FROM support_requests LIMIT 10 OFFSET %s", ((page - 1) * 10,))
    
    support_requests = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('admin/support.html', support_requests=support_requests, status=status)

@app.route('/admin/support/<int:request_id>/update', methods=['POST'])
@login_required
@admin_required
def admin_update_support(request_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM support_requests WHERE id = %s", (request_id,))
    support_request = cursor.fetchone()
    
    if not support_request:
        flash('Support request not found', 'error')
        return redirect(url_for('admin_support'))
    
    action = request.form.get('action')
    response = request.form.get('response', '')
    
    if action == 'close':
        if support_request['status'] != 'closed':
            cursor.execute("""
                UPDATE support_requests SET status = 'closed' WHERE id = %s
            """, (request_id,))
            
            # Create notification for the user
            cursor.execute("""
                INSERT INTO notifications (user_id, message, type, is_read, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                support_request['user_id'],
                f'Your support request has been closed. Response: {response}',
                'support_closed',
                False,
                datetime.utcnow()
            ))
            
            conn.commit()
            flash('Support request closed successfully', 'success')
        else:
            flash('Support request is already closed', 'info')
    elif action == 'reopen':
        if support_request['status'] != 'open':
            cursor.execute("""
                UPDATE support_requests SET status = 'open' WHERE id = %s
            """, (request_id,))
            
            # Create notification for the user
            cursor.execute("""
                INSERT INTO notifications (user_id, message, type, is_read, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                support_request['user_id'],
                'Your support request has been reopened',
                'support_reopened',
                False,
                datetime.utcnow()
            ))
            
            conn.commit()
            flash('Support request reopened successfully', 'success')
        else:
            flash('Support request is already open', 'info')
    
    cursor.close()
    conn.close()
    
    return redirect(url_for('admin_support'))

@app.context_processor
def inject_users_count():
    if current_user.is_authenticated and current_user.is_admin:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        return {'users': users}
    return {'users': []}

@app.route('/my_trips')
@login_required
def my_trips():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM trips WHERE user_id = %s", (current_user.id,))
    trips = cursor.fetchall()
    now = datetime.now().date()
    for trip in trips:
        trip['is_upcoming'] = trip['start_date'] > now
    cursor.close()
    conn.close()
    return render_template('my_trips.html', trips=trips)

@app.route('/admin/login', methods=['GET', 'POST'])
@limiter.limit("20 per minute")
def admin_login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return redirect(url_for('admin_login'))
            
        user = User.get_by_username(username)
        
        if user and check_password_hash(user.password_hash, password):
            if user.is_admin:
                login_user(user)
                flash('Admin login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('You do not have admin privileges.', 'error')
                return redirect(url_for('admin_login'))
        else:
            flash('Invalid admin credentials', 'error')
            
    return render_template('admin/login.html')

@app.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    if request.method == 'POST':
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        if not subject or not message:
            flash('Please fill in all fields', 'error')
            return redirect(url_for('contact'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create support request
        cursor.execute("""
            INSERT INTO support_requests (user_id, subject, message, status)
            VALUES (%s, %s, %s, %s)
        """, (current_user.id, subject, message, 'open'))
        
        # Create notification for all admins
        cursor.execute("SELECT id FROM users WHERE is_admin = TRUE")
        admins = cursor.fetchall()
        
        for admin in admins:
            cursor.execute("""
                INSERT INTO notifications (user_id, message, type, is_read, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                admin['id'],
                f'New support request from {current_user.username}: {subject}',
                'support_request',
                False,
                datetime.utcnow()
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        flash('Your message has been sent to the admin team. We will get back to you soon.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('contact.html')

@app.route('/admin/support_requests')
@login_required
@admin_required
def admin_support_requests():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM support_requests 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    requests = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin/support_requests.html', requests=requests)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/select_package', methods=['GET', 'POST'])
def select_package():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM tour_packages')
    packages = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('select_package.html', packages=packages)

@app.route('/packages', methods=['GET', 'POST'])
def packages():
    if request.method == 'POST':
        destination = request.form.get('destination')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM tour_packages WHERE city LIKE %s OR country LIKE %s",
            (f"%{destination}%", f"%{destination}%")
        )
        packages = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('select_package.html', packages=packages, destination=destination, start_date=start_date, end_date=end_date)
    return render_template('search_package.html')

@app.route('/book_package/<int:package_id>', methods=['GET', 'POST'])
@login_required
def book_package(package_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tour_packages WHERE id = %s", (package_id,))
    package = cursor.fetchone()
    cursor.close()
    conn.close()
    if request.method == 'POST':
        # Save booking in trips/payments table
        # Use package['price'], package['name'], etc.
        # ... (your booking logic here)
        flash('Booking successful!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('book_package.html', package=package)

@app.route('/admin/trip/<int:trip_id>/check_in', methods=['POST'])
@login_required
@admin_required
def admin_check_in_trip(trip_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM trips WHERE id = %s", (trip_id,))
    trip = cursor.fetchone()
    if not trip:
        cursor.close()
        conn.close()
        flash('Trip not found.', 'error')
        return redirect(url_for('admin_trips'))
    if trip['check_in_time']:
        cursor.close()
        conn.close()
        flash('Trip already checked in.', 'info')
        return redirect(url_for('admin_trips'))
    now = datetime.now()
    cursor2 = conn.cursor()
    cursor2.execute("UPDATE trips SET check_in_time = %s WHERE id = %s", (now, trip_id))
    conn.commit()
    cursor2.close()
    cursor.close()
    conn.close()
    flash('User checked in for the trip!', 'success')
    return redirect(url_for('admin_trips'))

if __name__ == '__main__':
    with app.app_context():
        try:
            # Create database and tables if they don't exist
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Create database if not exists
            cursor.execute("CREATE DATABASE IF NOT EXISTS travel_management")
            cursor.execute("USE travel_management")
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(256) NOT NULL,
                    first_name VARCHAR(50),
                    last_name VARCHAR(50),
                    is_admin BOOLEAN DEFAULT FALSE,
                    status VARCHAR(20) DEFAULT 'active',
                    profile_picture VARCHAR(255),
                    phone_number VARCHAR(20),
                    location VARCHAR(100),
                    date_of_birth DATE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    reset_token VARCHAR(100),
                    reset_token_expires DATETIME
                )
            """)
            
            # Create trips table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trips (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    destination VARCHAR(255) NOT NULL,
                    start_date DATE NOT NULL,
                    start_time TIME NOT NULL,
                    end_date DATE NOT NULL,
                    description TEXT,
                    status VARCHAR(20) DEFAULT 'active',
                    category VARCHAR(50),
                    tour_type VARCHAR(50),
                    long_tour_details TEXT,
                    short_tour_details TEXT,
                    amount DECIMAL(10,2),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Create payments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    trip_id INT NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    payment_method VARCHAR(50) NOT NULL,
                    transaction_id VARCHAR(100),
                    status VARCHAR(20) DEFAULT 'pending',
                    proof_file VARCHAR(255),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (trip_id) REFERENCES trips(id)
                )
            """)
            
            # Create notifications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    trip_id INT,
                    message TEXT NOT NULL,
                    type VARCHAR(50),
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (trip_id) REFERENCES trips(id)
                )
            """)
            
            # Create support_requests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS support_requests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    subject VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    status VARCHAR(20) DEFAULT 'open',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Create tour_packages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tour_packages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    country VARCHAR(100),
                    city VARCHAR(100),
                    nights INT,
                    days INT,
                    provider VARCHAR(100),
                    price INT,
                    currency VARCHAR(10) DEFAULT 'BDT',
                    hotel_class VARCHAR(20),
                    includes TEXT,
                    excludes TEXT,
                    website VARCHAR(255)
                )
            """)
            
            # Create district_tour_prices table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS district_tour_prices (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    district VARCHAR(100) NOT NULL,
                    division VARCHAR(100),
                    short_tour INT,
                    long_tour INT,
                    family_tour_per_person INT
                )
            """)
            
            # Create special_places table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS special_places (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    rate INT NOT NULL
                )
            """)
            
            # Insert special places
            cursor.execute("""
                INSERT INTO special_places (name, rate) VALUES
                ('Bandarban', 20000),
                ('Khagrachari', 18000),
                ('Sundarban', 25000)
                ON DUPLICATE KEY UPDATE rate=VALUES(rate);
            """)
            
            # Ensure admin user exists
            cursor.execute("SELECT * FROM users WHERE is_admin = TRUE LIMIT 1")
            admin = cursor.fetchone()
            if not admin:
                try:
                    cursor.execute("""
                        INSERT INTO users (username, email, password_hash, first_name, last_name, is_admin, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        'admin',
                        'admin@example.com',
                        generate_password_hash('admin123'),
                        'Admin',
                        'User',
                        True,
                        'active'
                    ))
                    print("Admin user created successfully. Username: admin, Password: admin123")
                except Error as e:
                    print(f"Error creating admin user: {e}")

            # Create a test regular user if not exists
            cursor.execute("SELECT * FROM users WHERE username = 'testuser' LIMIT 1")
            test_user = cursor.fetchone()
            if not test_user:
                try:
                    cursor.execute("""
                        INSERT INTO users (username, email, password_hash, first_name, last_name, is_admin, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        'testuser',
                        'test@example.com',
                        generate_password_hash('test123'),
                        'Test',
                        'User',
                        False,
                        'active'
                    ))
                    print("Test user created successfully. Username: testuser, Password: test123")
                except Error as e:
                    print(f"Error creating test user: {e}")
            
            # Insert tour packages
            cursor.execute("""
                INSERT INTO tour_packages (name, country, city, nights, days, provider, price, hotel_class, includes, excludes, website)
                VALUES
                ('Thailand (Bangkok & Phuket)', 'Thailand', 'Bangkok, Phuket', 4, 5, 'Arnim Holidays', 24900, '2-star', 'hotel stays, daily breakfast, city tours, airport transfers', 'visa fees, airfare', 'arnimholidays.com'),
                ('Thailand (Bangkok & Phuket)', 'Thailand', 'Bangkok, Phuket', 4, 5, 'M&N Holidays', 21500, NULL, 'stays in Bangkok and Phuket, city tours, transfers', 'visa fees, airfare', NULL),
                ('Malaysia (Kuala Lumpur & Langkawi)', 'Malaysia', 'Kuala Lumpur, Langkawi', 4, 5, 'Arnim Holidays', 45500, '2-star', 'return flights, accommodations, daily breakfast, tours', 'visa fees, tourism tax', 'arnimholidays.com'),
                ('India (Delhi, Shimla, Agra)', 'India', 'Delhi, Shimla, Agra', NULL, NULL, 'GreenHeaven Tours & Travels', NULL, NULL, 'various packages', 'contact for details', NULL),
                ('Japan', 'Japan', NULL, NULL, 4, 'ITS Holidays Ltd.', 145500, NULL, 'accommodations, tours', 'airfare', NULL),
                ('Cox''s Bazar', 'Bangladesh', 'Cox''s Bazar', 3, 4, 'ITS Holidays Ltd.', 17100, NULL, 'flights, hotel stays, transfers', NULL, 'itsholidaysltd.com'),
                ('Cox''s Bazar', 'Bangladesh', 'Cox''s Bazar', 3, 4, 'ITS Holidays Ltd.', 29500, NULL, 'flights, hotel stays, transfers', NULL, 'itsholidaysltd.com'),
                ('Cox''s Bazar', 'Bangladesh', 'Cox''s Bazar', 3, 4, 'Nagbak', 7900, NULL, 'accommodations, local tours', NULL, NULL),
                ('Sundarbans', 'Bangladesh', 'Sundarbans', 2, 3, 'Tourlink BD', 8500, NULL, 'transportation, accommodations, guided tours', NULL, NULL),
                ('Bandarban', 'Bangladesh', 'Bandarban', 3, 4, 'Nagbak', 4900, NULL, 'accommodations, sightseeing', NULL, NULL)
                ;
            """)
            
            # Insert district tour prices
            cursor.execute("""
                INSERT INTO district_tour_prices (district, division, short_tour, long_tour, family_tour_per_person) VALUES
                ('Dhaka', 'Dhaka', 5000, 25000, 28000),
                ('Foridpur', 'Dhaka', 5000, 25000, 28000),
                ('Gazipur', 'Dhaka', 5000, 25000, 28000),
                ('Gopalganj', 'Dhaka', 5000, 25000, 28000),
                ('Kishorganj', 'Dhaka', 5000, 25000, 28000);
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Error as e:
            print(f"Error during database initialization: {e}")
            
    # Start the application
    app.run(host='0.0.0.0', port=5000, debug=True)