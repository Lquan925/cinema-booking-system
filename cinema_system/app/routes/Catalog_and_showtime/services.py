from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from app.repositories import booking_repository


def list_movies():
    movies = booking_repository.get_all_movies()
    return [
        {
            "movie_id": movie.movie_id,
            "title": movie.title,
            "description": movie.description,
            "duration_minutes": movie.duration_minutes,
            "age_rating": movie.age_rating,
            "poster_url": movie.poster_url,
            "trailer_url": movie.trailer_url,
        }
        for movie in movies
    ]


def list_cinemas():
    cinemas = booking_repository.get_all_cinemas()
    return [
        {
            "cinema_id": cinema.cinema_id,
            "name": cinema.name,
            "address": cinema.address,
            "hotline": cinema.hotline,
        }
        for cinema in cinemas
    ]


def list_showtimes(date=None, movie_id=None, cinema_id=None):
    parsed_date = None
    if date is not None:
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("date phải có dạng YYYY-MM-DD")

        if parsed_date.strftime("%Y-%m-%d") != date:
            raise ValueError("date phải có dạng YYYY-MM-DD")

    def parse_id(value, field):
        if value is None:
            return None

        str_val = str(value)
        if not str_val.isascii() or not str_val.isdigit():
            raise ValueError(f"{field} phải là số nguyên dương")

        parsed_id = int(str_val)
        if parsed_id <= 0:
            raise ValueError(f"{field} phải là số nguyên dương")

        return parsed_id

    parsed_movie_id = parse_id(movie_id, "movie_id")
    parsed_cinema_id = parse_id(cinema_id, "cinema_id")

    showtimes = booking_repository.get_all_showtimes(
        movie_id=parsed_movie_id,
        cinema_id=parsed_cinema_id,
        date=parsed_date,
    )

    return [
        {
            "showtime_id": showtime.showtime_id,
            "movie_id": showtime.movie_id,
            "room_id": showtime.room_id,
            "cinema_id": (
                showtime.room.cinema_id
                if showtime.room is not None else None
            ),
            "start_time": (
                showtime.start_time.isoformat()
                if showtime.start_time is not None else None
            ),
            "end_time": (
                showtime.end_time.isoformat()
                if showtime.end_time is not None else None
            ),
            "price": (
                str(showtime.price)
                if showtime.price is not None else None
            ),
        }
        for showtime in showtimes
    ]


def add_movie(movie_data):
    title = movie_data.get("title")
    duration = movie_data.get("duration_minutes")

    if not isinstance(title, str) or not title.strip():
        raise ValueError("Tên phim không được để trống")

    if len(title.strip()) > 255:
        raise ValueError("Tên phim tối đa 255 ký tự")

    if type(duration) is not int or duration <= 0:
        raise ValueError("Thời lượng phải là số nguyên dương")

    for field, maximum in (
        ("description", None),
        ("age_rating", 10),
        ("poster_url", 255),
        ("trailer_url", 255),
    ):
        value = movie_data.get(field)

        if value is not None:
            if not isinstance(value, str):
                raise ValueError(f"{field} phải là chuỗi")

            if maximum is not None and len(value) > maximum:
                raise ValueError(f"{field} tối đa {maximum} ký tự")

    clean_data = {
        "title": title.strip(),
        "duration_minutes": duration,
        "description": movie_data.get("description"),
        "age_rating": movie_data.get("age_rating"),
        "poster_url": movie_data.get("poster_url"),
        "trailer_url": movie_data.get("trailer_url"),
    }

    movie, error = booking_repository.create_movie(**clean_data)
    if error or not movie:
        raise ValueError(f"Không thể tạo phim: {error}")

    return movie.movie_id


def add_showtime(showtime_data):
    movie_id = showtime_data.get("movie_id")
    room_id = showtime_data.get("room_id")

    if type(movie_id) is not int or movie_id <= 0:
        raise ValueError("movie_id phải là số nguyên dương")

    if type(room_id) is not int or room_id <= 0:
        raise ValueError("room_id phải là số nguyên dương")

    raw_start = showtime_data.get("start_time")

    if not isinstance(raw_start, str):
        raise ValueError("start_time phải là chuỗi ngày giờ")

    try:
        start_time = datetime.fromisoformat(raw_start)
    except ValueError:
        raise ValueError(
            "start_time phải có dạng 2026-10-10T19:00:00"
        )

    if start_time.tzinfo is not None:
        raise ValueError(
            "Dùng giờ Việt Nam không kèm offset trong phiên bản này"
        )

    vietnam_now = datetime.now(
        timezone(timedelta(hours=7))
    ).replace(tzinfo=None)

    if start_time <= vietnam_now:
        raise ValueError("Giờ bắt đầu phải nằm trong tương lai")

    raw_price = showtime_data.get("price")

    if isinstance(raw_price, bool) or not isinstance(
        raw_price, (str, int, float)
    ):
        raise ValueError("Giá vé không hợp lệ")

    try:
        price = Decimal(str(raw_price))
    except InvalidOperation:
        raise ValueError("Giá vé không hợp lệ")

    if (
        not price.is_finite()
        or price < 0
        or price > Decimal("99999999.99")
    ):
        raise ValueError("Giá vé nằm ngoài khoảng hợp lệ")

    if price != price.quantize(Decimal("0.01")):
        raise ValueError("Giá vé tối đa hai chữ số thập phân")

    room = booking_repository.get_room_by_id(room_id)
    if room is None:
        raise ValueError("Phòng chiếu không tồn tại")

    movie = booking_repository.get_movie_by_id(movie_id)
    if movie is None:
        raise ValueError("Phim không tồn tại")

    if not movie.duration_minutes or movie.duration_minutes <= 0:
        raise ValueError("Thời lượng phim không hợp lệ")

    end_time = start_time + timedelta(minutes=movie.duration_minutes)

    if booking_repository.check_overlapping_showtime(room_id, start_time, end_time):
        raise ValueError("Lịch chiếu trùng trong cùng phòng")

    showtime, error = booking_repository.create_showtime(
        start_time=start_time,
        end_time=end_time,
        price=price,
        movie_id=movie_id,
        room_id=room_id,
    )

    if error or not showtime:
        raise ValueError(f"Không thể tạo lịch chiếu: {error}")

    return showtime.showtime_id


def delete_showtime(showtime_id):
    showtime = booking_repository.get_showtime_by_id(showtime_id)
    if showtime is None:
        raise LookupError("Không tìm thấy suất chiếu")

    if booking_repository.has_tickets_for_showtime(showtime_id):
        raise ValueError("Không thể xóa suất chiếu đã có đơn/vé liên quan")

    success, error = booking_repository.delete_showtime(showtime)
    if not success:
        raise ValueError(f"Không thể xóa suất chiếu: {error}")