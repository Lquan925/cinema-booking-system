from flask import Blueprint, request, jsonify, g
from . import services
from .exceptions import (
    BookingError,
    RoomNotFound,
    SeatLockConflict,
    SeatLockForbidden,
    SeatLockUnavailable,
    ShowtimeNotFound,
    UserNotFound,
)

# Gắn tiền tố /api cho toàn bộ các route trong module này
booking_bp = Blueprint('booking', __name__, url_prefix='/api')


def _error_response(error):
    """Chuyển domain exception thành HTTP response tương ứng."""
    if isinstance(error, (ShowtimeNotFound, RoomNotFound, UserNotFound)):
        status_code = 404
    elif isinstance(error, SeatLockForbidden):
        status_code = 403
    elif isinstance(error, SeatLockConflict):
        status_code = 409
    elif isinstance(error, SeatLockUnavailable):
        status_code = 503
    else:
        status_code = 400
    return jsonify({"error": str(error)}), status_code


@booking_bp.route('/showtimes/<int:showtime_id>/seats', methods=['GET'])
def get_showtime_seats(showtime_id):
    """
    Load seat map and real-time availability for a showtime:
    - URL: GET /api/showtimes/<showtime_id>/seats
    - Query parameters (optional): ?user_id=<user_id>
    - Or automatically detected from Bearer Token (g.current_user)
    """
    current_user_id = request.args.get('user_id', type=int) or getattr(getattr(g, 'current_user', None), 'user_id', None)
    try:
        result = services.get_showtime_seats_service(showtime_id, current_user_id=current_user_id)
    except BookingError as error:
        return _error_response(error)
    return jsonify(result), 200


@booking_bp.route('/booking/lock-seat', methods=['POST'])
def api_lock_seat():
    """
    Temporarily lock seats into Redis (5 - 10 minutes):
    - URL: POST /api/booking/lock-seat
    - JSON Body:
        {
            "user_id": 5,          # Optional (counter staff pass customer ID, or auto-extracted from Auth Token)
            "showtime_id": 1,
            "seat_id": 15          # Lock 1 seat
            # OR "seat_ids": [15, 16] # Lock multiple seats
            # "ttl": 600           # Optional (default 600 seconds)
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

    try:
        result = services.lock_seat_service(user_id=user_id, showtime_id=showtime_id, seat_ids=seat_ids, ttl=ttl)
    except BookingError as error:
        return _error_response(error)
    return jsonify(result), 200


@booking_bp.route('/booking/unlock-seat', methods=['POST'])
def api_unlock_seat():
    """
    Unlock seats when expired or user cancels/switches seats:
    - URL: POST /api/booking/unlock-seat
    - JSON Body:
        {
            "user_id": 5,         # Optional (staff pass customer ID, or auto-extracted from Auth Token)
            "showtime_id": 1,
            "seat_id": 15         # Optional (unlock single seat)
            # OR "seat_ids": [15, 16] # Optional (unlock multiple seats)
            # If seat_id/seat_ids omitted: Unlocks ALL seats held by this user for this showtime
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

    try:
        result = services.unlock_seat_service(user_id=user_id, showtime_id=showtime_id, seat_ids=seat_ids)
    except BookingError as error:
        return _error_response(error)
    return jsonify(result), 200