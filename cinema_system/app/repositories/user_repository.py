"""
Kho lưu trữ người dùng (User Repository)
=========================================
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
    đảm bảo khóa chính VARCHAR(32) luôn có giá trị hợp lệ.
    """
    users = User.query.filter(User.user_id.like(f"{prefix}%")).all()
    max_num = 0
    for u in users:
        match = re.search(r'\d+', u.user_id)
        if match:
            num = int(match.group())
            if num > max_num:
                max_num = num

    if max_num > 0:
        candidate_id = f"{prefix}{max_num + 1:02d}"
        if not User.query.get(candidate_id):
            return candidate_id

    return f"{prefix}{uuid.uuid4().hex[:6].upper()}"


def get_by_id(user_id):
    """Tìm user theo primary key (user_id dạng VARCHAR như 'U01')"""
    if not user_id:
        return None
    return User.query.get(str(user_id))


def get_by_email(email):
    """Tìm user theo email"""
    if not email:
        return None
    return User.query.filter_by(email=email.strip().lower()).first()


def create(name, email, hashed_password, role='CUSTOMER', user_id=None):
    """
    Tạo user mới và lưu vào database.
    Hỗ trợ sinh mã user_id dạng 'Uxx' nếu không được truyền vào.
    Trả về (user, None) nếu thành công, (None, error_message) nếu thất bại.
    """
    try:
        final_user_id = user_id if user_id else generate_next_user_id(prefix="U")
        new_user = User(
            user_id=final_user_id,
            name=name.strip(),
            email=email.strip().lower(),
            password=hashed_password,
            role=role.upper() if role else 'CUSTOMER',
            loyalty_points=0,
            wallet_balance=0
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
    role: lọc theo vai trò
    search: tìm kiếm theo tên hoặc email
    page, per_page: phân trang
    Trả về (list_users, total_count)
    """
    query = User.query

    if role:
        query = query.filter_by(role=role.upper())

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

