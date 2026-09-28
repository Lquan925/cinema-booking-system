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

    @app.route('/')
    def index():
        return {"status": "success", "message": "Cinema Booking API is running!"}

    return app