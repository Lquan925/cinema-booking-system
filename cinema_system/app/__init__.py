import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-dev-key')

    db.init_app(app)
    migrate.init_app(app, db)
    # Đăng ký Models để Flask-Migrate nhận diện
    from app import models

    # ── Đăng ký Middleware (xác thực tập trung) ──
    from app.middleware.auth import init_auth_middleware
    init_auth_middleware(app)

    # ── Đăng ký tất cả Blueprints ──
    from app.routes.User_management.routes import user_bp
    from app.routes.Booking_and_seat.routes import booking_bp
    from app.routes.Catalog_and_showtime.routes import catalog_bp
    from app.routes.Orders_and_payments.routes import orders_bp
    from app.routes.Reports_and_Analytics.routes import admin_bp

    app.register_blueprint(user_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)

    @app.route('/')
    def index():
        return {"status": "success", "message": "Cinema Booking API is running!"}
    
    # Đăng ký Blueprint cho route
    
    from app.routes.User_management.routes import user_bp
    app.register_blueprint(user_bp)
    return app