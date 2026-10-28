"""Lỗi nghiệp vụ của module đặt vé / giữ ghế.

Service raise các exception này; tầng route chịu trách nhiệm
chuyển chúng thành HTTP status phù hợp.
"""


class BookingError(Exception):
    """Lỗi nghiệp vụ cơ sở của module đặt vé."""


class BookingValidationError(BookingError):
    """Dữ liệu đầu vào không hợp lệ."""


class ShowtimeNotFound(BookingError):
    """Suất chiếu không tồn tại."""


class RoomNotFound(BookingError):
    """Phòng chiếu không tồn tại."""


class UserNotFound(BookingError):
    """Người dùng không tồn tại."""


class SeatsNotInRoom(BookingError):
    """Có ghế không thuộc phòng chiếu của suất."""

    def __init__(self, message, invalid_seat_ids):
        super().__init__(message)
        self.invalid_seat_ids = invalid_seat_ids


class SeatAlreadySold(BookingError):
    """Ghế đã có vé (chưa hủy) trong suất chiếu."""

    def __init__(self, message, seat_id):
        super().__init__(message)
        self.seat_id = seat_id


class SeatQuotaExceeded(BookingError):
    """Vượt giới hạn số ghế được giữ đồng thời."""


class SeatLockConflict(BookingError):
    """Ghế đang bị người khác giữ."""

    def __init__(self, message, seat_id):
        super().__init__(message)
        self.seat_id = seat_id


class SeatLockForbidden(BookingError):
    """Không có quyền mở khóa ghế của người khác."""


class SeatLockUnavailable(BookingError):
    """Kho khóa ghế (Redis) không khả dụng."""
