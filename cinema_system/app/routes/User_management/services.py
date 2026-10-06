import hmac
import hashlib
import json
import base64
import time
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from app import db
from app.models import User

TOKEN_EXPIRATION_SECONDS = 86400

def _get_secret_key():
    return current_app.config.get('SECRET_KEY', 'default-cinema-secret-key').encode('utf-8')


def generate_token(user_id, role):
    """
    Tạo token xác thực bảo mật HMAC-SHA256.
    """
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': int(time.time()) + TOKEN_EXPIRATION_SECONDS
    }
    payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode('utf-8').rstrip('=')

    signature = hmac.new(_get_secret_key(), payload_b64.encode('utf-8'), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')

    return f"{payload_b64}.{sig_b64}"


def verify_token(token):
    """
    Xác thực token và lấy thông tin payload (user_id, role).
    Trả về dict payload nếu hợp lệ, None nếu token sai hoặc hết hạn.
    """
    if not token or '.' not in token:
        return None

    try:
        payload_b64, sig_b64 = token.split('.', 1)

        expected_sig = hmac.new(_get_secret_key(), payload_b64.encode('utf-8'), hashlib.sha256).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode('utf-8').rstrip('=')

        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return None

        # Bù padding base64
        padded_b64 = payload_b64 + '=' * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded_b64).decode('utf-8'))

        # Kiểm tra hết hạn
        if payload.get('exp', 0) < time.time():
            return None

        return payload
    except Exception:
        return None


def user_to_dict(user):
    """Chuyển đổi User model sang dictionary JSON an toàn."""
    return {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "loyalty_points": user.loyalty_points or 0,
        "wallet_balance": float(user.wallet_balance) if user.wallet_balance is not None else 0.0
    }


def register_user(name, email, password):
    """
    Nghiệp vụ Đăng ký tài khoản khách hàng mới
    """
    if not name or not email or not password:
        return False, "Vui lòng nhập đầy đủ họ tên, email và mật khẩu."

    email = email.strip().lower()
    if '@' not in email or '.' not in email:
        return False, "Email không hợp lệ."

    if len(password) < 6:
        return False, "Mật khẩu phải có ít nhất 6 ký tự."

    # Kiểm tra email đã tồn tại trong database chưa
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return False, "Email này đã được đăng ký tài khoản."

    # Băm mật khẩu an toàn
    hashed_password = generate_password_hash(password)

    # Tạo User mới với role mặc định là customer
    new_user = User(
        name=name.strip(),
        email=email,
        password=hashed_password,
        role='customer',
        loyalty_points=0,
        wallet_balance=0.0
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return True, user_to_dict(new_user)
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi hệ thống khi tạo tài khoản: {str(e)}"


def authenticate_user(email, password):
    """
    Nghiệp vụ Đăng nhập: Áp dụng cho Khách hàng, Nhân viên quầy và Admin
    """
    if not email or not password:
        return False, "Vui lòng nhập email và mật khẩu."

    email = email.strip().lower()
    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        return False, "Email hoặc mật khẩu không chính xác."

    # Tạo token xác thực
    token = generate_token(user.user_id, user.role)

    return True, {
        "token": token,
        "user": user_to_dict(user)
    }


def get_user_by_id(user_id):
    """Lấy thông tin người dùng theo user_id"""
    user = User.query.get(user_id)
    if not user:
        return None
    return user_to_dict(user)


def update_user_profile(user_id, name=None, password=None):
    """Cập nhật thông tin cá nhân (họ tên hoặc mật khẩu)"""
    user = User.query.get(user_id)
    if not user:
        return False, "Không tìm thấy người dùng."

    if name and name.strip():
        user.name = name.strip()

    if password:
        if len(password) < 6:
            return False, "Mật khẩu mới phải có ít nhất 6 ký tự."
        user.password = generate_password_hash(password)

    try:
        db.session.commit()
        return True, user_to_dict(user)
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi cập nhật thông tin: {str(e)}"


def get_all_users():
    """Lấy danh sách tất cả người dùng (Dành cho Admin)"""
    users = User.query.all()
    return [user_to_dict(u) for u in users]


def create_staff_user(name, email, password, role='staff'):
    """Admin cấp tài khoản cho nhân viên quầy"""
    if not name or not email or not password:
        return False, "Vui lòng nhập đầy đủ thông tin nhân viên."

    email = email.strip().lower()
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return False, "Email này đã tồn tại trong hệ thống."

    new_staff = User(
        name=name.strip(),
        email=email,
        password=generate_password_hash(password),
        role=role,
        loyalty_points=0,
        wallet_balance=0.0
    )

    try:
        db.session.add(new_staff)
        db.session.commit()
        return True, user_to_dict(new_staff)
    except Exception as e:
        db.session.rollback()
        return False, f"Lỗi khi tạo tài khoản nhân viên: {str(e)}"
