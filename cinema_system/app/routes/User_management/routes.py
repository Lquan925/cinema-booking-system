from flask import Blueprint, request, jsonify
from . import services

user_bp = Blueprint('users_management', __name__, url_prefix='/api')

@user_bp.route('/auth/register', methods=['POST'])
def register():
    pass

@user_bp.route('/auth/login', methods=['POST'])
def login():
    pass

@user_bp.route('/users/profile', methods=['GET'])
def profile():
    pass

@user_bp.route('/admin/users', methods=['GET'])
def admin_users():
    pass