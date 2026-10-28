"""
Reports and Analytics – Business Logic Layer (Services)
========================================================
Xử lý logic nghiệp vụ cho việc tạo báo cáo và phân tích:
  - Báo cáo doanh thu (theo thời gian, theo rạp, theo phim)
  - Báo cáo phim ăn khách (Top Movies Performance)
  - Báo cáo tổng quan Dashboard (Overview Summary)
  - Báo cáo hiệu suất theo từng rạp chiếu (Cinemas Performance)
Mọi tương tác với database đều thông qua analytics_repository.
"""
from datetime import datetime
from app.repositories import analytics_repository


def _parse_and_validate_date(date_str, field_name="date"):
    """Kiểm tra định dạng ngày YYYY-MM-DD"""
    if not date_str:
        return None, None
    try:
        parsed = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        # Đảm bảo không bị overflow/invalid (ví dụ 2026-02-30)
        if parsed.strftime("%Y-%m-%d") != date_str.strip():
            return None, f"Tham số '{field_name}' không hợp lệ. Vui lòng dùng định dạng YYYY-MM-DD!"
        return parsed, None
    except (ValueError, TypeError):
        return None, f"Tham số '{field_name}' không đúng định dạng YYYY-MM-DD!"


def _parse_positive_int(val, field_name, default=None):
    """Kiểm tra và chuyển đổi số nguyên dương"""
    if val is None or val == "":
        return default, None
    try:
        int_val = int(str(val).strip())
        if int_val <= 0:
            return None, f"Tham số '{field_name}' phải là số nguyên dương lớn hơn 0!"
        return int_val, None
    except (ValueError, TypeError):
        return None, f"Tham số '{field_name}' phải là một số nguyên hợp lệ!"


def get_revenue_report(start_date=None, end_date=None, cinema_id=None, movie_id=None):
    """
    Tạo báo cáo doanh thu với các bộ lọc:
    - start_date (YYYY-MM-DD)
    - end_date (YYYY-MM-DD)
    - cinema_id (int)
    - movie_id (int)
    """
    # 1. Kiểm tra định dạng ngày
    sd, err = _parse_and_validate_date(start_date, "start_date")
    if err:
        return False, err

    ed, err = _parse_and_validate_date(end_date, "end_date")
    if err:
        return False, err

    if sd and ed and sd > ed:
        return False, "Ngày bắt đầu ('start_date') không được lớn hơn ngày kết thúc ('end_date')!"

    # 2. Kiểm tra cinema_id và movie_id
    cid, err = _parse_positive_int(cinema_id, "cinema_id")
    if err:
        return False, err

    mid, err = _parse_positive_int(movie_id, "movie_id")
    if err:
        return False, err

    # 3. Lấy dữ liệu từ Repository
    try:
        data = analytics_repository.get_revenue_report_data(
            start_date=sd,
            end_date=ed,
            cinema_id=cid,
            movie_id=mid
        )
        return True, data
    except Exception as e:
        return False, f"Lỗi khi trích xuất dữ liệu doanh thu: {str(e)}"


def get_top_movies_report(start_date=None, end_date=None, limit=10):
    """
    Tạo báo cáo top phim có doanh thu và số lượng vé bán cao nhất
    """
    sd, err = _parse_and_validate_date(start_date, "start_date")
    if err:
        return False, err

    ed, err = _parse_and_validate_date(end_date, "end_date")
    if err:
        return False, err

    if sd and ed and sd > ed:
        return False, "Ngày bắt đầu ('start_date') không được lớn hơn ngày kết thúc ('end_date')!"

    limit_val, err = _parse_positive_int(limit, "limit", default=10)
    if err:
        return False, err

    if limit_val > 100:
        limit_val = 100

    try:
        data = analytics_repository.get_top_movies_report_data(
            start_date=sd,
            end_date=ed,
            limit=limit_val
        )
        return True, data
    except Exception as e:
        return False, f"Lỗi khi trích xuất dữ liệu top phim: {str(e)}"


def get_overview_report():
    """
    Tạo báo cáo tổng quan Dashboard dành cho Quản trị viên
    """
    try:
        data = analytics_repository.get_overview_report_data()
        return True, data
    except Exception as e:
        return False, f"Lỗi khi tạo báo cáo tổng quan: {str(e)}"


def get_cinema_performance_report(start_date=None, end_date=None):
    """
    Tạo báo cáo chi tiết hiệu suất kinh doanh của từng cụm rạp
    """
    sd, err = _parse_and_validate_date(start_date, "start_date")
    if err:
        return False, err

    ed, err = _parse_and_validate_date(end_date, "end_date")
    if err:
        return False, err

    if sd and ed and sd > ed:
        return False, "Ngày bắt đầu ('start_date') không được lớn hơn ngày kết thúc ('end_date')!"

    try:
        data = analytics_repository.get_cinema_performance_data(start_date=sd, end_date=ed)
        return True, data
    except Exception as e:
        return False, f"Lỗi khi lấy dữ liệu rạp: {str(e)}"
