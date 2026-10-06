from functools import wraps
from flask import Blueprint, request, jsonify
from . import services

user_bp = Blueprint('users_management', __name__, url_prefix='/api')

def token_required(f):
    """Decorator kiểm tra token xác thực người dùng"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                "status": "error",
                "message": "Vui lòng cung cấp token đăng nhập (Header 'Authorization: Bearer <token>')."
            }), 401

        token = auth_header.split(' ', 1)[1].strip()
        payload = services.verify_token(token)
        if not payload:
            return jsonify({
                "status": "error",
                "message": "Token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại."
            }), 401

        return f(payload, *args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator kiểm tra quyền Admin"""
    @wraps(f)
    def decorated(payload, *args, **kwargs):
        if payload.get('role') != 'admin':
            return jsonify({
                "status": "error",
                "message": "Từ chối truy cập: Chức năng này chỉ dành cho Admin."
            }), 403
        return f(payload, *args, **kwargs)
    return decorated


"""Register"""
@user_bp.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    success, result = services.register_user(name, email, password)
    if not success:
        return jsonify({
            "status": "error",
            "message": result
        }), 400

    return jsonify({
        "status": "success",
        "message": "Đăng ký tài khoản thành công!",
        "data": result
    }), 201

"""Login"""
@user_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    success, result = services.authenticate_user(email, password)
    if not success:
        return jsonify({
            "status": "error",
            "message": result
        }), 401

    return jsonify({
        "status": "success",
        "message": "Đăng nhập thành công!",
        "token": result["token"],
        "user": result["user"]
    }), 200

"""Profile"""
@user_bp.route('/users/profile', methods=['GET'])
@token_required
def get_profile(payload):
    user_id = payload.get('user_id')
    user_info = services.get_user_by_id(user_id)
    if not user_info:
        return jsonify({
            "status": "error",
            "message": "Không tìm thấy người dùng."
        }), 404

    return jsonify({
        "status": "success",
        "data": user_info
    }), 200


@user_bp.route('/users/profile', methods=['PUT'])
@token_required
def update_profile(payload):
    user_id = payload.get('user_id')
    data = request.get_json() or {}
    name = data.get('name')
    password = data.get('password')

    success, result = services.update_user_profile(user_id, name, password)
    if not success:
        return jsonify({
            "status": "error",
            "message": result
        }), 400

    return jsonify({
        "status": "success",
        "message": "Cập nhật thông tin thành công!",
        "data": result
    }), 200


"""Admin"""
@user_bp.route('/admin/users', methods=['GET'])
@token_required
@admin_required
def get_admin_users(payload):
    users = services.get_all_users()
    return jsonify({
        "status": "success",
        "total": len(users),
        "data": users
    }), 200


@user_bp.route('/admin/users', methods=['POST'])
@token_required
@admin_required
def create_staff(payload):
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'staff')

    success, result = services.create_staff_user(name, email, password, role)
    if not success:
        return jsonify({
            "status": "error",
            "message": result
        }), 400

    return jsonify({
        "status": "success",
        "message": f"Tạo tài khoản {role} thành công!",
        "data": result
    }), 201