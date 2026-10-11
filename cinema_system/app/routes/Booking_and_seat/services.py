from app import db
from app.models import Showtime, Room, Seat, Movie, Ticket, User
from app.redis_client import get_redis_client
import redis

# Hằng số cấu hình mặc định
DEFAULT_LOCK_TTL = 600       # 10 phút (600 giây)
MAX_SEATS_PER_USER = 8       # Giới hạn tối đa ghế một user được giữ cùng lúc trong 1 suất chiếu


def get_showtime_seats_service(showtime_id, current_user_id=None):
    """
    Tải sơ đồ ghế của một suất chiếu:
    - Lấy thông tin phòng và toàn bộ ghế từ MySQL.
    - Lấy danh sách vé đã mua từ MySQL (status != 'cancelled').
    - Kiểm tra trạng thái khóa tạm thời (realtime) từ Redis.
    """
    showtime = db.session.get(Showtime, showtime_id)
    if not showtime:
        return {"error": "Suất chiếu không tồn tại", "status_code": 404}

    room = db.session.get(Room, showtime.room_id)
    if not room:
        return {"error": "Phòng chiếu không tồn tại", "status_code": 404}

    movie = db.session.get(Movie, showtime.movie_id)
    movie_title = movie.title if movie else ""

    # Lấy tất cả ghế trong phòng, sắp xếp theo hàng và số ghế
    seats = Seat.query.filter_by(room_id=room.room_id).order_by(
        Seat.seat_row.asc(), Seat.seat_number.asc()
    ).all()

    # Lấy danh sách ghế đã được bán trong MySQL
    sold_tickets = Ticket.query.filter(
        Ticket.showtime_id == showtime_id,
        Ticket.status != 'cancelled'
    ).all()
    sold_seat_ids = {t.seat_id for t in sold_tickets}

    # Truy vấn trạng thái ghế từ Redis
    redis_client = get_redis_client()
    lock_keys = [f"seat_lock:{showtime_id}:{seat.seat_id}" for seat in seats]
    
    lock_values = []
    try:
        if lock_keys:
            lock_values = redis_client.mget(lock_keys)
    except (redis.exceptions.RedisError, Exception) as e:
        # Nếu Redis gặp sự cố, log và xử lý an toàn
        lock_values = [None] * len(seats)

    seats_data = []
    available_count = 0
    locked_count = 0
    sold_count = len(sold_seat_ids)

    for seat, lock_val, key in zip(seats, lock_values, lock_keys):
        if seat.seat_id in sold_seat_ids:
            seat_status = "sold"
            locked_by = None
            is_my_lock = False
            ttl_left = None
        elif lock_val is not None:
            seat_status = "locked"
            locked_by = int(lock_val) if str(lock_val).isdigit() else lock_val
            is_my_lock = bool(current_user_id and str(current_user_id) == str(lock_val))
            try:
                ttl_left = redis_client.ttl(key)
                if ttl_left and ttl_left < 0:
                    ttl_left = None
            except Exception:
                ttl_left = None
            locked_count += 1
        else:
            seat_status = "available"
            locked_by = None
            is_my_lock = False
            ttl_left = None
            available_count += 1

        seats_data.append({
            "seat_id": seat.seat_id,
            "seat_row": seat.seat_row,
            "seat_number": seat.seat_number,
            "seat_type": seat.seat_type,
            "price": float(showtime.price) if showtime.price is not None else 0.0,
            "status": seat_status,
            "locked_by": locked_by,
            "is_my_lock": is_my_lock,
            "expires_in_seconds": ttl_left
        })

    return {
        "status": "success",
        "data": {
            "showtime": {
                "showtime_id": showtime.showtime_id,
                "movie_id": showtime.movie_id,
                "movie_title": movie_title,
                "room_id": room.room_id,
                "room_name": room.name,
                "screen_type": room.screen_type,
                "start_time": showtime.start_time.isoformat() if showtime.start_time else None,
                "end_time": showtime.end_time.isoformat() if showtime.end_time else None,
                "base_price": float(showtime.price) if showtime.price is not None else 0.0
            },
            "summary": {
                "total_seats": len(seats),
                "available_seats": available_count,
                "locked_seats": locked_count,
                "sold_seats": sold_count
            },
            "seats": seats_data
        },
        "status_code": 200
    }


def lock_seat_service(user_id, showtime_id, seat_ids, ttl=DEFAULT_LOCK_TTL):
    """
    Khóa ghế tạm thời vào Redis (5 - 10 phút):
    - Kiểm tra User và Showtime tồn tại trong MySQL.
    - Kiểm tra các ghế có thuộc phòng chiếu của suất này không.
    - Kiểm tra các ghế đã được bán chưa (bảng Tickets trong MySQL).
    - Sử dụng Key 2 (user_locks:{user_id}:{showtime_id}) để giới hạn tối đa 6-8 ghế/user.
    - Sử dụng Key 1 (seat_lock:{showtime_id}:{seat_id}) với SET ... NX EX để khóa nguyên tử.
    - Rollback nếu một trong các ghế bị người khác chọn trước.
    """
    if not user_id:
        return {"error": "Thiếu user_id", "status_code": 400}
    if not showtime_id:
        return {"error": "Thiếu showtime_id", "status_code": 400}
    if not seat_ids or not isinstance(seat_ids, (list, set, tuple)):
        return {"error": "Danh sách seat_ids không hợp lệ hoặc đang để trống", "status_code": 400}

    # Loại bỏ trùng lặp trong input
    seat_ids = list(dict.fromkeys(seat_ids))

    # 1. Kiểm tra User tồn tại trong MySQL
    user = db.session.get(User, user_id)
    if not user:
        return {"error": f"Người dùng ID {user_id} không tồn tại", "status_code": 404}

    # 2. Kiểm tra Showtime tồn tại trong MySQL
    showtime = db.session.get(Showtime, showtime_id)
    if not showtime:
        return {"error": f"Suất chiếu ID {showtime_id} không tồn tại", "status_code": 404}

    # 3. Kiểm tra các ghế có thuộc phòng chiếu của suất này không
    valid_seats = Seat.query.filter(
        Seat.seat_id.in_(seat_ids),
        Seat.room_id == showtime.room_id
    ).all()
    if len(valid_seats) != len(seat_ids):
        valid_seat_ids = {s.seat_id for s in valid_seats}
        invalid_ids = [s for s in seat_ids if s not in valid_seat_ids]
        return {
            "error": f"Các ghế sau không thuộc phòng chiếu của suất này: {invalid_ids}",
            "status_code": 400
        }

    # 4. Kiểm tra ghế đã bán trong MySQL chưa
    sold_ticket = Ticket.query.filter(
        Ticket.showtime_id == showtime_id,
        Ticket.seat_id.in_(seat_ids),
        Ticket.status != 'cancelled'
    ).first()
    if sold_ticket:
        return {
            "error": f"Ghế ID {sold_ticket.seat_id} đã được đặt mua trước đó, không thể giữ chỗ.",
            "status_code": 400
        }

    redis_client = get_redis_client()
    user_locks_key = f"user_locks:{user_id}:{showtime_id}"

    # 5. Kiểm tra giới hạn ghế đang giữ của User (Key 2)
    try:
        current_held_raw = redis_client.smembers(user_locks_key) or set()
        # Đồng bộ hóa: kiểm tra xem các ghế trong set này còn thực sự bị lock không
        active_held = set()
        for sid in current_held_raw:
            lock_owner = redis_client.get(f"seat_lock:{showtime_id}:{sid}")
            if lock_owner == str(user_id):
                active_held.add(sid)
            else:
                # Key 1 đã hết hạn, dọn dẹp khỏi set
                redis_client.srem(user_locks_key, sid)

        # Số ghế mới user muốn giữ thêm (không tính các ghế user vốn dĩ đang giữ)
        new_seat_ids = [sid for sid in seat_ids if str(sid) not in active_held]
        if len(active_held) + len(new_seat_ids) > MAX_SEATS_PER_USER:
            return {
                "error": f"Bạn chỉ được giữ tối đa {MAX_SEATS_PER_USER} ghế cùng lúc cho suất chiếu này. Hiện bạn đang giữ {len(active_held)} ghế.",
                "status_code": 400
            }

        # 6. Khóa từng ghế vào Redis bằng lệnh SET ... NX EX (Key 1)
        successfully_locked = []
        for sid in seat_ids:
            seat_lock_key = f"seat_lock:{showtime_id}:{sid}"
            
            # Nếu chính user này đang giữ ghế này rồi thì chỉ cần refresh TTL
            if str(sid) in active_held:
                redis_client.expire(seat_lock_key, ttl)
                successfully_locked.append(sid)
                continue

            # Sử dụng lệnh SET ... NX EX (nguyên tử)
            acquired = redis_client.set(seat_lock_key, str(user_id), nx=True, ex=ttl)
            if not acquired:
                # Có người khác đã chọn ghế này trước!
                # Thực hiện ROLLBACK các ghế vừa lock trong đợt này
                for rolled_sid in successfully_locked:
                    if str(rolled_sid) not in active_held:
                        redis_client.delete(f"seat_lock:{showtime_id}:{rolled_sid}")
                        redis_client.srem(user_locks_key, str(rolled_sid))
                return {
                    "error": f"Ghế ID {sid} đã có người khác chọn hoặc đang được giữ chỗ.",
                    "status_code": 409
                }
            
            successfully_locked.append(sid)
            # Thêm vào Key 2 (Set các ghế user đang giữ)
            redis_client.sadd(user_locks_key, str(sid))

        # Cập nhật thời gian sống cho Key 2
        redis_client.expire(user_locks_key, ttl)

        all_user_seats = [int(s) for s in redis_client.smembers(user_locks_key)]

        return {
            "status": "success",
            "message": "Khóa ghế thành công. Vui lòng hoàn tất thanh toán trong thời gian quy định.",
            "data": {
                "user_id": user_id,
                "showtime_id": showtime_id,
                "locked_seats": successfully_locked,
                "expires_in_seconds": ttl,
                "total_holding_seats": all_user_seats
            },
            "status_code": 200
        }

    except redis.exceptions.RedisError as e:
        return {
            "error": "Lỗi kết nối dịch vụ Redis, không thể thực hiện giữ ghế lúc này.",
            "status_code": 503
        }


def unlock_seat_service(user_id, showtime_id, seat_ids=None):
    """
    Mở khóa ghế khi khách hủy hoặc hết giờ hoặc thanh toán xong:
    - Nếu có seat_ids: Mở khóa danh sách ghế được chỉ định (kiểm tra quyền sở hữu lock).
    - Nếu seat_ids=None: Đọc từ Key 2 (user_locks:{user_id}:{showtime_id}) và mở khóa toàn bộ.
    """
    if not user_id:
        return {"error": "Thiếu user_id", "status_code": 400}
    if not showtime_id:
        return {"error": "Thiếu showtime_id", "status_code": 400}

    redis_client = get_redis_client()
    user_locks_key = f"user_locks:{user_id}:{showtime_id}"

    try:
        unlocked_seats = []

        if seat_ids is not None:
            # Chuẩn hóa seat_ids thành danh sách
            if not isinstance(seat_ids, (list, set, tuple)):
                seat_ids = [seat_ids]

            for sid in seat_ids:
                seat_lock_key = f"seat_lock:{showtime_id}:{sid}"
                current_holder = redis_client.get(seat_lock_key)

                if current_holder is None:
                    # Ghế đã tự hết hạn hoặc chưa bị khóa
                    redis_client.srem(user_locks_key, str(sid))
                    unlocked_seats.append(sid)
                elif current_holder == str(user_id):
                    # Xóa Key 1
                    redis_client.delete(seat_lock_key)
                    # Xóa khỏi Key 2
                    redis_client.srem(user_locks_key, str(sid))
                    unlocked_seats.append(sid)
                else:
                    # Ghế đang do người khác giữ, không được phép mở
                    return {
                        "error": f"Bạn không có quyền mở khóa ghế ID {sid} vì đang do người khác giữ.",
                        "status_code": 403
                    }

            # Nếu tập hợp trống thì xóa luôn Key 2
            if redis_client.scard(user_locks_key) == 0:
                redis_client.delete(user_locks_key)

        else:
            # Mở khóa TẤT CẢ các ghế mà user đang giữ cho suất chiếu này
            held_seats = redis_client.smembers(user_locks_key) or set()
            for sid in held_seats:
                seat_lock_key = f"seat_lock:{showtime_id}:{sid}"
                current_holder = redis_client.get(seat_lock_key)
                if current_holder == str(user_id):
                    redis_client.delete(seat_lock_key)
                unlocked_seats.append(int(sid) if str(sid).isdigit() else sid)

            # Xóa Key 2
            redis_client.delete(user_locks_key)

        return {
            "status": "success",
            "message": "Mở khóa ghế thành công",
            "data": {
                "user_id": user_id,
                "showtime_id": showtime_id,
                "unlocked_seats": unlocked_seats
            },
            "status_code": 200
        }

    except redis.exceptions.RedisError as e:
        return {
            "error": "Lỗi kết nối dịch vụ Redis, không thể mở khóa ghế lúc này.",
            "status_code": 503
        }
