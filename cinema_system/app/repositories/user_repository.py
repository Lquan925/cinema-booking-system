"""
Kho lưu trữ người dùng (User Repository)
=========================================
Chịu trách nhiệm toàn bộ thao tác CRUD với bảng Users.
Services chỉ gọi các hàm ở đây, không truy cập db.session trực tiếp.
"""
from app import db
from app.models import User


def get_by_id(user_id):
    """Tìm user theo primary key"""
    return User.query.get(user_id)


def get_by_email(email):
    """Tìm user theo email"""
    return User.query.filter_by(email=email).first()


def create(name, email, hashed_password, role='customer'):
    """
    Tạo user mới và lưu vào database.
    Trả về (user, None) nếu thành công, (None, error_message) nếu thất bại.
    """
    try:
        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            role=role,
            loyalty_points=0,
            wallet_balance=0.0
        )
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
        query = query.filter_by(role=role)

    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
        )

    if page and per_page:
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        return pagination.items, pagination.total

    users = query.all()
    return users, len(users)
