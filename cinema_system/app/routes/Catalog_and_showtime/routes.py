from flask import Blueprint, request, jsonify, g
from . import services

catalog_bp = Blueprint('catalog', __name__, url_prefix='/api')

@catalog_bp.route('/movies', methods=['GET'])
def list_movies():
    movies = services.list_movies()
    return jsonify({"data": movies}), 200

@catalog_bp.route('/cinemas', methods=['GET'])
def list_cinemas():
    cinemas = services.list_cinemas()
    return jsonify({"data": cinemas}), 200

@catalog_bp.route('/showtimes', methods=['GET'])
def list_showtimes():
    try:
        showtimes = services.list_showtimes(
            date=request.args.get("date"),
            movie_id=request.args.get("movie_id"),
            cinema_id=request.args.get("cinema_id"),
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({"data": showtimes}), 200

@catalog_bp.route('/movies', methods=['POST'])
def add_movie():
    """
    Header: Authorization: Bearer <token_admin>
    """
    # 1. Trích xuất thông tin người dùng từ Token xác thực bảo mật
    user = getattr(g, 'current_user', None)
    if not user:
        return jsonify({
            "status": "error",
            "message": "Token xác thực không được cung cấp (Vui lòng gửi Header Authorization: Bearer <token>)!"
        }), 401

    # 2. Kiểm tra phân quyền: Chức năng chỉ dành riêng cho Quản trị viên (Admin)
    if (getattr(user, 'role', '') or '').lower() != 'admin':
        return jsonify({
            "status": "error",
            "message": "Quyền truy cập bị từ chối. Chức năng chỉ dành cho Quản trị viên!"
        }), 403

    admin_id = user.user_id

    # 3. Kiểm tra định dạng dữ liệu đầu vào
    if not request.is_json:
        return jsonify({
            "error": "Cần gửi application/json"
        }), 415

    movie_data = request.get_json(silent=True)

    if not isinstance(movie_data, dict):
        return jsonify({
            "error": "Body phải là JSON object hợp lệ"
        }), 400

    try:
        movie_id = services.add_movie(movie_data, admin_id=admin_id)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({
        "message": "Movie added successfully",
        "movie_id": movie_id,
    }), 201

@catalog_bp.route('/showtimes', methods=['POST'])
def add_showtime():
    """
    Header: Authorization: Bearer <token_admin>
    """
    # 1. Trích xuất thông tin người dùng từ Token xác thực bảo mật
    user = getattr(g, 'current_user', None)
    if not user:
        return jsonify({
            "status": "error",
            "message": "Token xác thực không được cung cấp (Vui lòng gửi Header Authorization: Bearer <token>)!"
        }), 401

    # 2. Kiểm tra phân quyền: Chức năng chỉ dành riêng cho Quản trị viên (Admin)
    if (getattr(user, 'role', '') or '').lower() != 'admin':
        return jsonify({
            "status": "error",
            "message": "Quyền truy cập bị từ chối. Chức năng chỉ dành cho Quản trị viên!"
        }), 403

    admin_id = user.user_id

    # 3. Kiểm tra định dạng dữ liệu đầu vào
    if not request.is_json:
        return jsonify({
            "error": "Cần gửi application/json"
        }), 415

    showtime_data = request.get_json(silent=True)

    if not isinstance(showtime_data, dict):
        return jsonify({
            "error": "Body phải là JSON object hợp lệ"
        }), 400

    try:
        showtime_id = services.add_showtime(showtime_data, admin_id=admin_id)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({
        "message": "Showtime added successfully",
        "showtime_id": showtime_id,
    }), 201

@catalog_bp.route('/showtimes/<int:showtime_id>', methods=['DELETE'])
def delete_showtime(showtime_id):
    """
    [Xóa suất chiếu chưa có đơn/vé liên quan]
    Quyền: Quản trị viên (Admin)
    Header: Authorization: Bearer <token_admin>
    """
    # 1. Trích xuất thông tin người dùng từ Token xác thực bảo mật
    user = getattr(g, 'current_user', None)
    if not user:
        return jsonify({
            "status": "error",
            "message": "Token xác thực không được cung cấp (Vui lòng gửi Header Authorization: Bearer <token>)!"
        }), 401

    # 2. Kiểm tra phân quyền: Chức năng chỉ dành riêng cho Quản trị viên (Admin)
    if (getattr(user, 'role', '') or '').lower() != 'admin':
        return jsonify({
            "status": "error",
            "message": "Quyền truy cập bị từ chối. Chức năng chỉ dành cho Quản trị viên!"
        }), 403

    admin_id = user.user_id

    try:
        services.delete_showtime(showtime_id, admin_id=admin_id)
    except LookupError as error:
        return jsonify({"error": str(error)}), 404
    except ValueError as error:
        return jsonify({"error": str(error)}), 409

    return "", 204