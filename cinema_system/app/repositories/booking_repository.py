"""
Kho lưu trữ Đặt vé / Danh mục / Đơn hàng (Booking Repository)
================================================================
Chịu trách nhiệm toàn bộ thao tác CRUD với các bảng:
  - Movies, Cinemas, Rooms, Seats, Showtimes  (Danh mục)
  - Tickets                                    (Đặt vé)
  - Orders                                     (Đơn hàng)
Services chỉ gọi các hàm ở đây, không truy cập db.session trực tiếp.
"""
from app import db
from app.models import Movie, Cinema, Room, Seat, Showtime, Ticket, Order


# ──────────────────────────────────────────────
#  MOVIE (Phim)
# ──────────────────────────────────────────────

def get_movie_by_id(movie_id):
    """Lấy thông tin phim theo ID"""
    return Movie.query.get(movie_id)


def get_all_movies():
    """Lấy danh sách tất cả phim"""
    return Movie.query.all()


def create_movie(title, description, duration_minutes, age_rating, poster_url=None, trailer_url=None):
    """Thêm phim mới vào database"""
    try:
        movie = Movie(
            title=title,
            description=description,
            duration_minutes=duration_minutes,
            age_rating=age_rating,
            poster_url=poster_url,
            trailer_url=trailer_url
        )
        db.session.add(movie)
        db.session.commit()
        return movie, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)


# ──────────────────────────────────────────────
#  CINEMA & ROOM (Rạp & Phòng chiếu)
# ──────────────────────────────────────────────

def get_all_cinemas():
    """Lấy danh sách tất cả rạp phim"""
    return Cinema.query.all()


def get_cinema_by_id(cinema_id):
    """Lấy thông tin rạp theo ID"""
    return Cinema.query.get(cinema_id)


def get_room_by_id(room_id):
    """Lấy thông tin phòng chiếu theo ID"""
    return Room.query.get(room_id)


# ──────────────────────────────────────────────
#  SHOWTIME (Suất chiếu)
# ──────────────────────────────────────────────

def get_showtime_by_id(showtime_id):
    """Lấy suất chiếu theo ID"""
    return Showtime.query.get(showtime_id)


def get_all_showtimes(movie_id=None, cinema_id=None):
    """
    Lấy danh sách suất chiếu, có thể lọc theo movie_id hoặc cinema_id.
    """
    query = Showtime.query
    if movie_id:
        query = query.filter_by(movie_id=movie_id)
    if cinema_id:
        query = query.join(Room).filter(Room.cinema_id == cinema_id)
    return query.all()


def create_showtime(start_time, end_time, price, movie_id, room_id):
    """Tạo suất chiếu mới"""
    try:
        showtime = Showtime(
            start_time=start_time,
            end_time=end_time,
            price=price,
            movie_id=movie_id,
            room_id=room_id
        )
        db.session.add(showtime)
        db.session.commit()
        return showtime, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)


# ──────────────────────────────────────────────
#  SEAT (Ghế ngồi)
# ──────────────────────────────────────────────

def get_seat_by_id(seat_id):
    """Lấy thông tin ghế theo ID"""
    return Seat.query.get(seat_id)


def get_seats_by_room(room_id):
    """Lấy danh sách ghế trong 1 phòng chiếu"""
    return Seat.query.filter_by(room_id=room_id).all()


def get_seats_by_showtime(showtime_id):
    """
    Lấy tất cả ghế của phòng chiếu ứng với 1 suất chiếu.
    Kèm trạng thái ghế (đã đặt hay chưa) dựa vào bảng Tickets.
    """
    showtime = Showtime.query.get(showtime_id)
    if not showtime:
        return None

    seats = Seat.query.filter_by(room_id=showtime.room_id).all()

    # Lấy danh sách seat_id đã có ticket cho suất chiếu này
    booked_seat_ids = {
        t.seat_id for t in
        Ticket.query.filter_by(showtime_id=showtime_id)
              .filter(Ticket.status.in_(['pending', 'ready']))
              .all()
    }

    result = []
    for seat in seats:
        result.append({
            'seat_id': seat.seat_id,
            'seat_row': seat.seat_row,
            'seat_number': seat.seat_number,
            'seat_type': seat.seat_type,
            'status': 'booked' if seat.seat_id in booked_seat_ids else 'available'
        })

    return result


# ──────────────────────────────────────────────
#  TICKET (Vé)
# ──────────────────────────────────────────────

def get_ticket_by_id(ticket_id):
    """Lấy vé theo ID"""
    return Ticket.query.get(ticket_id)


def get_tickets_by_ids(ticket_ids):
    """Lấy danh sách vé theo list ID"""
    return Ticket.query.filter(Ticket.ticket_id.in_(ticket_ids)).all()


def get_tickets_by_order(order_id):
    """Lấy tất cả vé thuộc 1 đơn hàng"""
    return Ticket.query.filter_by(order_id=order_id).all()


def create_ticket(ticket_price, showtime_id, seat_id, status='pending'):
    """Tạo vé mới"""
    try:
        ticket = Ticket(
            ticket_price=ticket_price,
            showtime_id=showtime_id,
            seat_id=seat_id,
            status=status
        )
        db.session.add(ticket)
        db.session.commit()
        return ticket, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)


def update_ticket(ticket, **kwargs):
    """Cập nhật thông tin vé"""
    try:
        for key, value in kwargs.items():
            if hasattr(ticket, key) and value is not None:
                setattr(ticket, key, value)
        db.session.commit()
        return ticket, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)


# ──────────────────────────────────────────────
#  ORDER (Đơn hàng)
# ──────────────────────────────────────────────

def get_order_by_id(order_id):
    """Lấy đơn hàng theo ID"""
    return Order.query.get(order_id)


def get_orders_by_user(user_id):
    """Lấy tất cả đơn hàng của 1 người dùng"""
    return Order.query.filter_by(user_id=user_id).all()


def create_order(user_id, total_amount, status='pending'):
    """
    Tạo đơn hàng mới.
    Dùng flush() để lấy order_id trước khi commit (gắn ticket).
    """
    try:
        order = Order(
            user_id=user_id,
            total_amount=total_amount,
            status=status
        )
        db.session.add(order)
        db.session.flush()  # Lấy order_id ngay
        return order, None
    except Exception as e:
        db.session.rollback()#Hủy bọ toàn bộ các thay đổi đang được thực hiện dở
        return None, str(e)


def update_order(order, **kwargs):
    """Cập nhật trạng thái đơn hàng"""
    try:
        for key, value in kwargs.items():
            if hasattr(order, key) and value is not None:
                setattr(order, key, value)
        db.session.commit()
        return order, None
    except Exception as e:
        db.session.rollback()
        return None, str(e)


def commit():
    """Commit session hiện tại (dùng khi cần commit batch thay đổi)"""
    db.session.commit()


def rollback():
    """Rollback session hiện tại"""
    db.session.rollback()
