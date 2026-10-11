"""
Authentication & Authorization Middleware
==========================================
Xác thực và phân quyền tập trung cho toàn bộ ứng dụng.

Cách hoạt động:
  1. Đăng ký middleware vào Flask app qua hàm init_auth_middleware(app)
  2. Mỗi request đi qua before_request hook → tự động kiểm tra token
  3. Các route CÔNG KHAI (public) được liệt kê trong PUBLIC_ENDPOINTS → bỏ qua xác thực
  4. Các route CẦN QUYỀN ADMIN được liệt kê trong ADMIN_ENDPOINTS → kiểm tra role

Ưu điểm:
  - Không cần viết decorator @token_required, @admin_required trên từng endpoint
  - Thêm/bớt route cần bảo vệ chỉ cần sửa danh sách tại 1 chỗ
  - Đúng pattern middleware/interceptor theo yêu cầu kiến trúc
"""
from flask import request, jsonify, g
from app.repositories import user_repository


# ──────────────────────────────────────────────
#  CẤU HÌNH: Danh sách endpoint công khai & admin
# ──────────────────────────────────────────────

# Các endpoint KHÔNG cần đăng nhập (method, path_prefix)
PUBLIC_ENDPOINTS = [
    ('GET',  '/'),                          # Health check
    ('POST', '/api/auth/register'),         # Đăng ký
    ('POST', '/api/auth/login'),            # Đăng nhập
    ('GET',  '/api/movies'),                # Xem danh sách phim
    ('GET',  '/api/cinemas'),               # Xem danh sách rạp
    ('GET',  '/api/showtimes'),             # Xem lịch chiếu
]

# Các endpoint CHỈ DÀNH CHO ADMIN (method, path_prefix)
ADMIN_ENDPOINTS = [
    ('GET',  '/api/admin/'),                # Tất cả route /api/admin/*
    ('POST', '/api/admin/'),
    ('PUT',  '/api/admin/'),
    ('DELETE', '/api/admin/'),
]


# ──────────────────────────────────────────────
#  TOKEN UTILITIES
# ──────────────────────────────────────────────

def _extract_token_from_request():
    """
    Trích xuất token từ request header.
    Hỗ trợ: Authorization: Bearer <token>, x-access-token, X-User-Id (dev fallback)
    """
    # 1. Thử Authorization: Bearer <token>
    auth_header = request.headers.get('Authorization')
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            return parts[1]
        elif len(parts) == 1:
            return parts[0]

    # 2. Thử x-access-token header
    if 'x-access-token' in request.headers:
        return request.headers.get('x-access-token')

    return None


def _resolve_user_from_token(token, app):
    """Giải mã token và trả về User object, hoặc None nếu không hợp lệ"""
    from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

    secret_key = app.config.get('SECRET_KEY', 'default-dev-key')
    s = URLSafeTimedSerializer(secret_key)
    try:
        data = s.loads(token, max_age=86400)  # Token hết hạn sau 24 giờ
        user_id = data.get('user_id')
        if not user_id:
            return None
        return user_repository.get_by_id(user_id)
    except (SignatureExpired, BadSignature):
        return None


# ──────────────────────────────────────────────
#  KIỂM TRA ENDPOINT
# ──────────────────────────────────────────────

def _is_public_endpoint(method, path):
    """Kiểm tra request hiện tại có phải endpoint công khai không"""
    for pub_method, pub_path in PUBLIC_ENDPOINTS:
        if method == pub_method and path.rstrip('/') == pub_path.rstrip('/'):
            return True
    return False


def _is_admin_endpoint(method, path):
    """Kiểm tra request hiện tại có yêu cầu quyền Admin không"""
    for admin_method, admin_path in ADMIN_ENDPOINTS:
        if method == admin_method and path.startswith(admin_path):
            return True
    return False


# ──────────────────────────────────────────────
#  ĐĂNG KÝ MIDDLEWARE VÀO FLASK APP
# ──────────────────────────────────────────────

def init_auth_middleware(app):
    """
    Đăng ký authentication middleware vào Flask app.
    Gọi hàm này trong create_app() ở __init__.py.

    Luồng xử lý mỗi request:
      1. Endpoint công khai? → Cho qua
      2. Trích xuất token → Không có? → 401
      3. Giải mã token → Không hợp lệ? → 401
      4. Gán g.current_user
      5. Endpoint admin? → Kiểm tra role → Không phải admin? → 403
      6. Cho qua ✅
    """

    @app.before_request
    def authenticate():
        method = request.method
        path = request.path

        # ── Bước 1: Bỏ qua endpoint công khai ──
        if _is_public_endpoint(method, path):
            return None  # Cho qua, không cần xác thực

        # ── Bước 2: Trích xuất token ──
        token = _extract_token_from_request()

        # Fallback: dev test nhanh bằng X-User-Id
        if not token and request.headers.get('X-User-Id'):
            try:
                user_id = int(request.headers.get('X-User-Id'))
                user = user_repository.get_by_id(user_id)
                if user:
                    g.current_user = user
                    # Vẫn cần kiểm tra admin nếu endpoint yêu cầu
                    if _is_admin_endpoint(method, path) and user.role != 'admin':
                        return jsonify({
                            'status': 'error',
                            'message': 'Quyền truy cập bị từ chối. Chức năng chỉ dành cho Quản trị viên!'
                        }), 403
                    return None
            except (ValueError, TypeError):
                pass

        if not token:
            return jsonify({
                'status': 'error',
                'message': 'Token xác thực không được cung cấp (Vui lòng gửi Header Authorization: Bearer <token>)!'
            }), 401

        # ── Bước 3: Giải mã và xác minh token ──
        user = _resolve_user_from_token(token, app)
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'Token không hợp lệ hoặc đã hết hạn!'
            }), 401

        # ── Bước 4: Gán user vào context ──
        g.current_user = user

        # ── Bước 5: Kiểm tra quyền Admin ──
        if _is_admin_endpoint(method, path) and user.role != 'admin':
            return jsonify({
                'status': 'error',
                'message': 'Quyền truy cập bị từ chối. Chức năng chỉ dành cho Quản trị viên!'
            }), 403

        # ── Bước 6: Cho qua ✅ ──
        return None
