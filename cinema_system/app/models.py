from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'Users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(255))
    role = db.Column(db.String(20), default='customer')
    loyalty_points = db.Column(db.Integer, default=0)
    wallet_balance = db.Column(db.Numeric(10, 2), default=0)

    # Quan hệ 1-N với bảng Orders
    orders = db.relationship('Order', backref='user', lazy=True)

class Cinema(db.Model):
    __tablename__ = 'Cinemas'
    cinema_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100))
    address = db.Column(db.String(255))
    hotline = db.Column(db.String(20))

    # Quan hệ 1-N với bảng Rooms
    rooms = db.relationship('Room', backref='cinema', lazy=True)

class Room(db.Model):
    __tablename__ = 'Rooms'
    room_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50))
    screen_type = db.Column(db.String(50))
    cinema_id = db.Column(db.Integer, db.ForeignKey('Cinemas.cinema_id'))

    # Quan hệ 1-N với bảng Seats và Showtimes
    seats = db.relationship('Seat', backref='room', lazy=True)
    showtimes = db.relationship('Showtime', backref='room', lazy=True)

class Seat(db.Model):
    __tablename__ = 'Seats'
    seat_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    seat_row = db.Column(db.String(10))
    seat_number = db.Column(db.Integer)
    seat_type = db.Column(db.String(50))
    room_id = db.Column(db.Integer, db.ForeignKey('Rooms.room_id'))

    # Quan hệ 1-N với bảng Tickets
    tickets = db.relationship('Ticket', backref='seat', lazy=True)

class Movie(db.Model):
    __tablename__ = 'Movies'
    movie_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    duration_minutes = db.Column(db.Integer)
    age_rating = db.Column(db.String(10))
    poster_url = db.Column(db.String(255))
    trailer_url = db.Column(db.String(255))

    # Quan hệ 1-N với bảng Showtimes
    showtimes = db.relationship('Showtime', backref='movie', lazy=True)

class Showtime(db.Model):
    __tablename__ = 'Showtimes'
    showtime_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    price = db.Column(db.Numeric(10, 2))
    movie_id = db.Column(db.Integer, db.ForeignKey('Movies.movie_id'))
    room_id = db.Column(db.Integer, db.ForeignKey('Rooms.room_id'))

    # Quan hệ 1-N với bảng Tickets
    tickets = db.relationship('Ticket', backref='showtime', lazy=True)

class Order(db.Model):
    __tablename__ = 'Orders'
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    total_amount = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'))

    # Quan hệ 1-N với bảng Tickets
    tickets = db.relationship('Ticket', backref='order', lazy=True)

class Ticket(db.Model):
    __tablename__ = 'Tickets'
    ticket_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ticket_price = db.Column(db.Numeric(10, 2))
    qr_code_url = db.Column(db.String(255))
    status = db.Column(db.String(50))
    order_id = db.Column(db.Integer, db.ForeignKey('Orders.order_id'))
    showtime_id = db.Column(db.Integer, db.ForeignKey('Showtimes.showtime_id'))
    seat_id = db.Column(db.Integer, db.ForeignKey('Seats.seat_id'))