from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, time, timedelta

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    date_of_birth = db.Column(db.Date)
    phone_number = db.Column(db.String(20))
    location = db.Column(db.String(100))
    profile_picture = db.Column(db.String(255))
    status = db.Column(db.String(10), default='active')
    is_admin = db.Column(db.Boolean, default=False)
    trips = db.relationship('Trip', backref='user', lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def is_administrator(self):
        return self.is_admin

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    transaction_id = db.Column(db.String(100), nullable=True)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    proof_file = db.Column(db.String(255), nullable=True)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id', ondelete='CASCADE'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    destination = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=True)
    end_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(20), default='active')
    amount = db.Column(db.Float, nullable=True)
    check_in_time = db.Column(db.DateTime, nullable=True)
    category = db.Column(db.String(30), nullable=True)
    tour_type = db.Column(db.String(30), nullable=True)
    long_tour_details = db.Column(db.Text, nullable=True)
    short_tour_details = db.Column(db.Text, nullable=True)
    notifications = db.relationship('Notification', backref='trip', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='trip', lazy=True, cascade='all, delete-orphan')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def is_past(self):
        return self.start_date < datetime.now().date()

    def is_ongoing(self):
        today = datetime.now().date()
        return self.start_date <= today <= self.end_date

    def is_upcoming(self):
        return self.start_date > datetime.now().date()

    def is_missed(self):
        now = datetime.now()
        if not self.start_time:
            self.start_time = time(12, 0)
            db.session.commit()
        trip_start = datetime.combine(self.start_date, self.start_time)
        return now > trip_start + timedelta(hours=1) and not self.check_in_time

    def time_until_start(self):
        if not self.start_time:
            self.start_time = time(12, 0)
            db.session.commit()
        trip_start = datetime.combine(self.start_date, self.start_time)
        now = datetime.now()
        if trip_start > now:
            return trip_start - now
        return None

class SupportRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='support_requests') 