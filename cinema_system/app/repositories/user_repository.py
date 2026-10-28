"""
Kho lưu trữ người dùng
Chịu trách nhiệm toàn bộ thao tác CRUD với bảng Users.
Services chỉ gọi các hàm ở đây, không truy cập db.session trực tiếp.
"""
import re
import uuid
from app import db
from app.models import User


def generate_next_user_id(prefix="U"):
    """
    Tự động sinh mã user_id kế tiếp (U01, U02, ..., U07, ...)
    đảm bảo khóa chính có giá trị hợp lệ nếu dùng định dạng chuỗi.
    """
    try:
        users = User.query.all()
        max_num = 0
        for u in users:
            uid_str = str(u.user_id)
            match = re.search(r'\d+', uid_str)
            if match:
                num = int(match.group())
                if num > max_num:
                    max_num = num

        if max_num > 0:
            candidate_id = f"{prefix}{max_num + 1:02d}"
            if not User.query.get(candidate_id):
                return candidate_id

        return f"{prefix}{uuid.uuid4().hex[:6].upper()}"
    except Exception:
        return f"{prefix}01"


def get_by_id(user_id):
    """Tìm user theo primary key (hỗ trợ cả int và str)"""
    if not user_id:
        return None
    user = User.query.get(user_id)
    if not user and str(user_id).isdigit():
        user = User.query.get(int(user_id))
    return user


def get_by_email(email):
    """Tìm user theo email"""
    if not email:
        return None
    return User.query.filter_by(email=email.strip().lower()).first()


def create(name, email, hashed_password, role='CUSTOMER', user_id=None):
    """
    Tạo user mới và lưu vào database.
    Hỗ trợ truyền user_id hoặc để database tự sinh (autoincrement).
    Trả về (user, None) nếu thành công, (None, error_message) nếu thất bại.
    """
    try:
        user_kwargs = {
            'name': name.strip() if name else '',
            'email': email.strip().lower() if email else '',
            'password': hashed_password,
            'role': role.upper() if role else 'CUSTOMER',
            'loyalty_points': 0,
            'wallet_balance': 0.0
        }
        if user_id is not None:
            user_kwargs['user_id'] = user_id

        new_user = User(**user_kwargs)
        db.session.add(new_user)
        db.session.commit()
        return new_user, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)


def update(user, **kwargs):
    """
    Cập nhật các trường của user.
    Truyền vào keyword arguments tương ứng với tên cột cần update.
    Ví dụ: update(user, name="Tên mới", password=hashed_pw)
    """
    try:
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        db.session.commit()
        return user, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)


def get_all(role=None, search=None, page=None, per_page=None):
    """
    Lấy danh sách người dùng với các bộ lọc tuỳ chọn.
    - role: lọc theo vai trò
    - search: tìm kiếm theo tên hoặc email
    - page, per_page: phân trang
    Trả về (list_users, total_count)
    """
    query = User.query

    if role:
        query = query.filter(User.role.ilike(role.strip()))

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            (User.name.ilike(search_term)) | (User.email.ilike(search_term))
        )

    if page and per_page:
        pagination = query.paginate(page=int(page), per_page=int(per_page), error_out=False)
        return pagination.items, pagination.total

    users = query.all()
    return users, len(users)


def delete(user):
    """
    Xóa người dùng khỏi database.
    Trả về (True, None) nếu thành công, (False, error_message) nếu thất bại.
    """
    try:
        db.session.delete(user)
        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        return False, str(e)

