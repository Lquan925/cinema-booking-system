"""Nghiệp vụ đặt vé / giữ ghế.

Tầng này chỉ giao tiếp với repository (MySQL + kho khóa ghế Redis)
và raise domain exception; không import Flask, SQLAlchemy hay redis.
"""
from app.repositories import booking_repository, seat_lock_repository, user_repository
from app.repositories.seat_lock_repository import SeatLockStoreError

from .exceptions import (
    BookingValidationError,
    RoomNotFound,
    SeatAlreadySold,
    SeatLockConflict,
    SeatLockForbidden,
    SeatLockUnavailable,
    SeatQuotaExceeded,
    SeatsNotInRoom,
    ShowtimeNotFound,
    UserNotFound,
)

# Hằng số cấu hình mặc định
DEFAULT_LOCK_TTL = 600       # 10 phút (600 giây)
MAX_SEATS_PER_USER = 8       # Giới hạn tối đa ghế một user được giữ cùng lúc trong 1 suất chiếu


def get_showtime_seats_service(showtime_id, current_user_id=None):
    """
    Tải sơ đồ ghế của một suất chiếu:
    - Lấy thông tin phòng và toàn bộ ghế từ MySQL.
    - Lấy danh sách vé đã mua từ MySQL (status != 'cancelled').
    - Kiểm tra trạng thái khóa tạm thời (realtime) từ kho khóa Redis.
    """
    showtime = booking_repository.get_showtime_by_id(showtime_id)
    if not showtime:
        raise ShowtimeNotFound("Suất chiếu không tồn tại")

    room = booking_repository.get_room_by_id(showtime.room_id)
    if not room:
        raise RoomNotFound("Phòng chiếu không tồn tại")

    movie = booking_repository.get_movie_by_id(showtime.movie_id)
    movie_title = movie.title if movie else ""

    seats = booking_repository.get_seats_by_room(room.room_id)
    sold_seat_ids = booking_repository.get_ticket_seat_ids_by_showtime(showtime_id)

    seat_ids = [seat.seat_id for seat in seats]
    try:
        holders = seat_lock_repository.get_holders(showtime_id, seat_ids)
    except SeatLockStoreError:
        # Redis sự cố: vẫn trả sơ đồ ghế, coi như không có khóa tạm thời
        holders = {}

    seats_data = []
    available_count = 0
    locked_count = 0
    sold_count = len(sold_seat_ids)

    for seat in seats:
        lock_val = holders.get(seat.seat_id)

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
                ttl_left = seat_lock_repository.get_ttl(showtime_id, seat.seat_id)
            except SeatLockStoreError:
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
        }
    }


def lock_seat_service(user_id, showtime_id, seat_ids, ttl=DEFAULT_LOCK_TTL):
    """
    Khóa ghế tạm thời vào Redis (5 - 10 phút):
    - Kiểm tra User và Showtime tồn tại.
    - Kiểm tra các ghế có thuộc phòng chiếu của suất này không.
    - Kiểm tra các ghế đã được bán chưa.
    - Giới hạn số ghế một user được giữ cùng lúc.
    - Khóa nguyên tử từng ghế, rollback nếu có ghế bị người khác giữ trước.
    """
    if not user_id:
        raise BookingValidationError("Thiếu user_id")
    if not showtime_id:
        raise BookingValidationError("Thiếu showtime_id")
    if not seat_ids or not isinstance(seat_ids, (list, set, tuple)):
        raise BookingValidationError("Danh sách seat_ids không hợp lệ hoặc đang để trống")

    # Loại bỏ trùng lặp trong input
    seat_ids = list(dict.fromkeys(seat_ids))

    user = user_repository.get_by_id(user_id)
    if not user:
        raise UserNotFound(f"Người dùng ID {user_id} không tồn tại")

    showtime = booking_repository.get_showtime_by_id(showtime_id)
    if not showtime:
        raise ShowtimeNotFound(f"Suất chiếu ID {showtime_id} không tồn tại")

    valid_seats = booking_repository.get_seats_by_ids(seat_ids, room_id=showtime.room_id)
    if len(valid_seats) != len(seat_ids):
        valid_seat_ids = {seat.seat_id for seat in valid_seats}
        invalid_ids = [seat_id for seat_id in seat_ids if seat_id not in valid_seat_ids]
        raise SeatsNotInRoom(
            f"Các ghế sau không thuộc phòng chiếu của suất này: {invalid_ids}",
            invalid_seat_ids=invalid_ids,
        )

    sold_ticket = booking_repository.get_active_ticket_for_seats(showtime_id, seat_ids)
    if sold_ticket:
        raise SeatAlreadySold(
            f"Ghế ID {sold_ticket.seat_id} đã được đặt mua trước đó, không thể giữ chỗ.",
            seat_id=sold_ticket.seat_id,
        )

    try:
        current_held_raw = seat_lock_repository.get_user_locked_seats(user_id, showtime_id)

        # Đồng bộ: chỉ giữ lại các ghế thực sự còn khóa thuộc về user này
        active_held = set()
        for seat_id in current_held_raw:
            holder = seat_lock_repository.get_holder(showtime_id, seat_id)
            if holder == str(user_id):
                active_held.add(seat_id)
            else:
                seat_lock_repository.remove_user_locked_seat(user_id, showtime_id, seat_id)

        new_seat_ids = [seat_id for seat_id in seat_ids if str(seat_id) not in active_held]
        if len(active_held) + len(new_seat_ids) > MAX_SEATS_PER_USER:
            raise SeatQuotaExceeded(
                f"Bạn chỉ được giữ tối đa {MAX_SEATS_PER_USER} ghế cùng lúc cho suất chiếu này. "
                f"Hiện bạn đang giữ {len(active_held)} ghế."
            )

        successfully_locked = []
        for seat_id in seat_ids:
            # Ghế user đang giữ rồi: chỉ gia hạn TTL
            if str(seat_id) in active_held:
                seat_lock_repository.refresh(showtime_id, seat_id, ttl)
                successfully_locked.append(seat_id)
                continue

            if not seat_lock_repository.acquire(showtime_id, seat_id, user_id, ttl):
                # Người khác đã giữ ghế này: rollback các ghế vừa khóa trong đợt này
                for rolled_seat_id in successfully_locked:
                    if str(rolled_seat_id) not in active_held:
                        seat_lock_repository.release(showtime_id, rolled_seat_id)
                        seat_lock_repository.remove_user_locked_seat(user_id, showtime_id, rolled_seat_id)
                raise SeatLockConflict(
                    f"Ghế ID {seat_id} đã có người khác chọn hoặc đang được giữ chỗ.",
                    seat_id=seat_id,
                )

            successfully_locked.append(seat_id)
            seat_lock_repository.add_user_locked_seat(user_id, showtime_id, seat_id)

        seat_lock_repository.expire_user_locks(user_id, showtime_id, ttl)

        held_seats = seat_lock_repository.get_user_locked_seats(user_id, showtime_id)
        all_user_seats = sorted(int(seat_id) for seat_id in held_seats)

        return {
            "status": "success",
            "message": "Khóa ghế thành công. Vui lòng hoàn tất thanh toán trong thời gian quy định.",
            "data": {
                "user_id": user_id,
                "showtime_id": showtime_id,
                "locked_seats": successfully_locked,
                "expires_in_seconds": ttl,
                "total_holding_seats": all_user_seats
            }
        }

    except SeatLockStoreError:
        raise SeatLockUnavailable(
            "Lỗi kết nối dịch vụ Redis, không thể thực hiện giữ ghế lúc này."
        ) from None


def unlock_seat_service(user_id, showtime_id, seat_ids=None):
    """
    Mở khóa ghế khi khách hủy hoặc hết giờ hoặc thanh toán xong:
    - Nếu có seat_ids: Mở khóa danh sách ghế được chỉ định (kiểm tra quyền sở hữu lock).
    - Nếu seat_ids=None: Mở khóa toàn bộ ghế user đang giữ cho suất chiếu này.
    """
    if not user_id:
        raise BookingValidationError("Thiếu user_id")
    if not showtime_id:
        raise BookingValidationError("Thiếu showtime_id")

    try:
        unlocked_seats = []

        if seat_ids is not None:
            # Chuẩn hóa seat_ids thành danh sách
            if not isinstance(seat_ids, (list, set, tuple)):
                seat_ids = [seat_ids]

            for seat_id in seat_ids:
                current_holder = seat_lock_repository.get_holder(showtime_id, seat_id)

                if current_holder is None:
                    # Ghế đã tự hết hạn hoặc chưa bị khóa
                    seat_lock_repository.remove_user_locked_seat(user_id, showtime_id, seat_id)
                    unlocked_seats.append(seat_id)
                elif current_holder == str(user_id):
                    seat_lock_repository.release(showtime_id, seat_id)
                    seat_lock_repository.remove_user_locked_seat(user_id, showtime_id, seat_id)
                    unlocked_seats.append(seat_id)
                else:
                    raise SeatLockForbidden(
                        f"Bạn không có quyền mở khóa ghế ID {seat_id} vì đang do người khác giữ."
                    )

            if seat_lock_repository.count_user_locks(user_id, showtime_id) == 0:
                seat_lock_repository.delete_user_locks(user_id, showtime_id)

        else:
            # Mở khóa TẤT CẢ các ghế mà user đang giữ cho suất chiếu này
            held_seats = seat_lock_repository.get_user_locked_seats(user_id, showtime_id)
            for seat_id in held_seats:
                if seat_lock_repository.get_holder(showtime_id, seat_id) == str(user_id):
                    seat_lock_repository.release(showtime_id, seat_id)
                unlocked_seats.append(int(seat_id) if str(seat_id).isdigit() else seat_id)

            seat_lock_repository.delete_user_locks(user_id, showtime_id)

        return {
            "status": "success",
            "message": "Mở khóa ghế thành công",
            "data": {
                "user_id": user_id,
                "showtime_id": showtime_id,
                "unlocked_seats": unlocked_seats
            }
        }

    except SeatLockStoreError:
        raise SeatLockUnavailable(
            "Lỗi kết nối dịch vụ Redis, không thể mở khóa ghế lúc này."
        ) from None
