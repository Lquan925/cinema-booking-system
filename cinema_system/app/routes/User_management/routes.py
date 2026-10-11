from flask import Blueprint, request, jsonify, g
from . import services

user_bp = Blueprint('users_management', __name__, url_prefix='/api')

"""Các API xác thực công khai không cần token"""
@user_bp.route('/auth/register', methods=['POST'])
def register():
    """
    [Khách hàng đăng ký tài khoản]
    Body (JSON): { "name": "...", "email": "...", "password": "..." }
    """
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


@user_bp.route('/auth/login', methods=['POST'])
def login():
    """
    [Đăng nhập hệ thống - Cấp Token]
    Body (JSON): { "email": "...", "password": "..." }
    Trả về token để client gửi kèm trong header: 'Authorization: Bearer <token>'
    """
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

"""Các API cần token xác thực"""
@user_bp.route('/users/profile', methods=['GET'])
def get_profile():
    """
    [Xem thông tin cá nhân, điểm tích lũy & số dư ví]
    Header: Authorization: Bearer <token>
    (Middleware app/middleware/auth.py đã tự động giải mã token và gán vào g.current_user)
    """
    user = getattr(g, 'current_user', None)
    if not user:
        return jsonify({
            "status": "error",
            "message": "Không tìm thấy phiên đăng nhập."
        }), 401

    return jsonify({
        "status": "success",
        "data": services.user_to_dict(user)
    }), 200


@user_bp.route('/users/profile', methods=['PUT'])
def update_profile():
    """
    [Cập nhật họ tên hoặc đổi mật khẩu]
    Header: Authorization: Bearer <token>
    """
    user = getattr(g, 'current_user', None)
    if not user:
        return jsonify({
            "status": "error",
            "message": "Không tìm thấy phiên đăng nhập."
        }), 401

    data = request.get_json() or {}
    name = data.get('name')
    password = data.get('password')

    success, result = services.update_user_profile(user.user_id, name, password)
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

"""Các API dành riêng cho Admin"""
@user_bp.route('/admin/users', methods=['GET'])
def get_admin_users():
    """
    [Admin xem danh sách toàn bộ người dùng & nhân viên]
    Header: Authorization: Bearer <token_admin>
    (Middleware app/middleware/auth.py tự động chặn 403 nếu role không phải ADMIN)
    """
    role = request.args.get('role')
    search = request.args.get('search')
    page = request.args.get('page')
    per_page = request.args.get('per_page')

    users, total = services.get_all_users(role=role, search=search, page=page, per_page=per_page)
    return jsonify({
        "status": "success",
        "total": total,
        "data": users
    }), 200


@user_bp.route('/admin/users', methods=['POST'])
def create_staff():
    """
    [Admin cấp tài khoản mới cho nhân viên quầy]
    Header: Authorization: Bearer <token_admin>
    """
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'STAFF')

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