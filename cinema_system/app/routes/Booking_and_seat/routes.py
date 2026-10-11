from flask import Blueprint, request, jsonify, g
from . import services

# Gắn tiền tố /api cho toàn bộ các route trong module này
booking_bp = Blueprint('booking', __name__, url_prefix='/api')


@booking_bp.route('/showtimes/<int:showtime_id>/seats', methods=['GET'])
def get_showtime_seats(showtime_id):
    """
    Tải sơ đồ ghế của một suất chiếu:
    - URL: GET /api/showtimes/<showtime_id>/seats
    - Query params (tùy chọn): ?user_id=<user_id>
    - Hoặc tự động nhận diện từ Token xác thực (g.current_user)
    """
    current_user_id = request.args.get('user_id', type=int) or getattr(getattr(g, 'current_user', None), 'user_id', None)
    result = services.get_showtime_seats_service(showtime_id, current_user_id=current_user_id)
    status_code = result.pop('status_code', 200)
    return jsonify(result), status_code


@booking_bp.route('/booking/lock-seat', methods=['POST'])
def api_lock_seat():
    """
    Khóa ghế tạm thời vào Redis (5 - 10 phút):
    - URL: POST /api/booking/lock-seat
    - Body JSON:
        {
            "user_id": 5,          # Tùy chọn (nhân viên quầy truyền ID khách, hoặc tự lấy từ Auth Token)
            "showtime_id": 1,
            "seat_id": 15          # Khóa 1 ghế
            # HOẶC "seat_ids": [15, 16] # Khóa nhiều ghế
            # "ttl": 600           # Tùy chọn (mặc định 600 giây)
        }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Dữ liệu JSON không hợp lệ hoặc thiếu body", "status": "error"}), 400

    # Ưu tiên user_id truyền trong body, nếu không có thì lấy từ Auth Token
    user_id = data.get('user_id') or getattr(getattr(g, 'current_user', None), 'user_id', None)
    showtime_id = data.get('showtime_id')

    # Hỗ trợ cả 2 cách gửi: 'seat_id' (1 ghế) hoặc 'seat_ids' (danh sách)
    if 'seat_ids' in data:
        seat_ids = data.get('seat_ids')
    elif 'seat_id' in data:
        seat_ids = [data.get('seat_id')]
    else:
        seat_ids = []

    ttl = data.get('ttl', services.DEFAULT_LOCK_TTL)
    try:
        ttl = int(ttl)
        if ttl <= 0:
            ttl = services.DEFAULT_LOCK_TTL
    except (ValueError, TypeError):
        ttl = services.DEFAULT_LOCK_TTL

    result = services.lock_seat_service(user_id=user_id, showtime_id=showtime_id, seat_ids=seat_ids, ttl=ttl)
    status_code = result.pop('status_code', 200)
    return jsonify(result), status_code


@booking_bp.route('/booking/unlock-seat', methods=['POST'])
def api_unlock_seat():
    """
    Mở khóa ghế nếu hết giờ hoặc khách hủy:
    - URL: POST /api/booking/unlock-seat
    - Body JSON:
        {
            "user_id": 5,         # Tùy chọn (nhân viên quầy truyền ID khách, hoặc tự lấy từ Auth Token)
            "showtime_id": 1,
            "seat_id": 15         # Tùy chọn (mở 1 ghế)
            # HOẶC "seat_ids": [15, 16] # Tùy chọn (mở nhiều ghế)
            # Nếu không truyền seat_id/seat_ids: Mở khóa TẤT CẢ ghế user đang giữ ở suất chiếu này
        }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Dữ liệu JSON không hợp lệ hoặc thiếu body", "status": "error"}), 400

    user_id = data.get('user_id') or getattr(getattr(g, 'current_user', None), 'user_id', None)
    showtime_id = data.get('showtime_id')

    seat_ids = None
    if 'seat_ids' in data:
        seat_ids = data.get('seat_ids')
    elif 'seat_id' in data:
        seat_ids = [data.get('seat_id')]

    result = services.unlock_seat_service(user_id=user_id, showtime_id=showtime_id, seat_ids=seat_ids)
    status_code = result.pop('status_code', 200)
    return jsonify(result), status_code