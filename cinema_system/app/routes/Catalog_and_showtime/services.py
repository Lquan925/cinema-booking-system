from sqlalchemy import select
from app import db
from app.models import Movie, Cinema, Room, Showtime, Ticket
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation


class CatalogRepository:
    def list_movies(self):
        movies = db.session.execute(
            select(Movie).order_by(Movie.movie_id)
        ).scalars().all()

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

    def list_cinemas(self):
        cinemas = db.session.execute(
            select(Cinema).order_by(Cinema.cinema_id)
        ).scalars().all()

        return [
            {
                "cinema_id": cinema.cinema_id,
                "name": cinema.name,
                "address": cinema.address,
                "hotline": cinema.hotline,
            }
            for cinema in cinemas
        ]

    def list_showtimes(
        self,
        start_time=None,
        end_time=None,
        movie_id=None,
        cinema_id=None,
    ):
        query = select(Showtime)

        if start_time is not None:
            query = query.where(
                Showtime.start_time >= start_time,
                Showtime.start_time < end_time,
            )

        if movie_id is not None:
            query = query.where(
                Showtime.movie_id == movie_id
            )

        if cinema_id is not None:
            query = query.join(
                Room, Showtime.room_id == Room.room_id
            ).where(
                Room.cinema_id == cinema_id
            )

        showtimes = db.session.execute(
            query.order_by(
                Showtime.start_time,
                Showtime.showtime_id,
            )
        ).scalars().all()

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

    def add_movie(self, movie_data):
        try:
            new_movie = Movie(**movie_data)
            db.session.add(new_movie)
            db.session.commit()
            return new_movie.movie_id
        except Exception:
            db.session.rollback()
            raise

    def add_showtime(self, showtime_data):
        try:
            # Khóa phòng trong transaction để tránh hai request
            # cùng tạo lịch trùng trong một phòng.
            room = db.session.execute(
                select(Room)                
                .where(Room.room_id == showtime_data["room_id"])
                .with_for_update()
            ).scalar_one_or_none()

            if room is None:
                raise ValueError("Phòng chiếu không tồn tại")

            movie = db.session.get(
                Movie, showtime_data["movie_id"]
            )

            if movie is None:
                raise ValueError("Phim không tồn tại")

            if not movie.duration_minutes or movie.duration_minutes <= 0:
                raise ValueError("Thời lượng phim không hợp lệ")

            start_time = showtime_data["start_time"]
            end_time = start_time + timedelta(
                minutes=movie.duration_minutes
            )

            existing_id = db.session.execute(
                select(Showtime.showtime_id)
                .where(
                    Showtime.room_id == room.room_id,
                    Showtime.start_time < end_time,
                    Showtime.end_time > start_time,
                )
                .limit(1)
            ).scalar_one_or_none()

            if existing_id is not None:
                raise ValueError("Lịch chiếu trùng trong cùng phòng")

            new_showtime = Showtime(
                movie_id=movie.movie_id,
                room_id=room.room_id,
                start_time=start_time,
                end_time=end_time,
                price=showtime_data["price"],
            )

            db.session.add(new_showtime)
            db.session.flush()
            showtime_id = new_showtime.showtime_id
            db.session.commit()

            return showtime_id

        except Exception:
            db.session.rollback()
            raise

    def delete_showtime(self, showtime_id):
        try:
            showtime = db.session.execute(
                select(Showtime)
                .where(Showtime.showtime_id == showtime_id)
                .with_for_update()
            ).scalar_one_or_none()

            if showtime is None:
                raise LookupError("Không tìm thấy suất chiếu", 404)

            ticket_id = db.session.execute(
                select(Ticket.ticket_id)
                .where(Ticket.showtime_id == showtime_id)
                .limit(1)
            ).scalar_one_or_none()

            if ticket_id is not None:
                raise ValueError(
                    "Không thể xóa suất chiếu đã có đơn/vé liên quan",
                    409,
                )

            db.session.delete(showtime)
            db.session.commit()

        except Exception:
            db.session.rollback()
            raise



repository = CatalogRepository()


def list_movies():
    return repository.list_movies()

def list_cinemas():
    return repository.list_cinemas()

def list_showtimes(date=None, movie_id=None, cinema_id=None):
    start_time = None
    end_time = None

    if date is not None:
        try:
            parsed_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("date phải có dạng YYYY-MM-DD")

        if parsed_date.strftime("%Y-%m-%d") != date:
            raise ValueError("date phải có dạng YYYY-MM-DD")

        start_time = parsed_date
        end_time = start_time + timedelta(days=1)

    def parse_id(value, field):
        if value is None:
            return None

        if not value.isascii() or not value.isdigit():
            raise ValueError(f"{field} phải là số nguyên dương")

        parsed_id = int(value)

        if parsed_id <= 0:
            raise ValueError(f"{field} phải là số nguyên dương")

        return parsed_id

    return repository.list_showtimes(
        start_time=start_time,
        end_time=end_time,
        movie_id=parse_id(movie_id, "movie_id"),
        cinema_id=parse_id(cinema_id, "cinema_id"),
    )

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

    return repository.add_movie(clean_data)

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

    return repository.add_showtime({
        "movie_id": movie_id,
        "room_id": room_id,
        "start_time": start_time,
        "price": price,
    })

def delete_showtime(showtime_id):
    repository.delete_showtime(showtime_id)