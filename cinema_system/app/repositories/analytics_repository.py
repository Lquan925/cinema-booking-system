"""
Analytics & Reports – Data Access Layer (Repository)
=====================================================
Chịu trách nhiệm thực hiện các truy vấn tổng hợp dữ liệu báo cáo, thống kê và phân tích:
  - Báo cáo doanh thu (theo thời gian, theo rạp, theo phim)
  - Báo cáo hiệu suất phim (Top movies, số vé bán, doanh thu)
  - Thống kê tổng quan hệ thống (Dashboard Overview)
  - Thống kê hiệu suất theo cụm rạp
"""
from datetime import datetime, timedelta
from sqlalchemy import func, distinct, desc
from app import db
from app.models import Order, Ticket, Showtime, Movie, Room, Cinema, User


def _build_date_range(start_date=None, end_date=None):
    """Chuyển đổi start_date, end_date sang đối tượng datetime đầy đủ"""
    start_dt = None
    end_dt = None

    if start_date:
        if isinstance(start_date, str):
            sd = datetime.strptime(start_date, "%Y-%m-%d").date()
        elif isinstance(start_date, datetime):
            sd = start_date.date()
        else:
            sd = start_date
        start_dt = datetime(sd.year, sd.month, sd.day, 0, 0, 0)

    if end_date:
        if isinstance(end_date, str):
            ed = datetime.strptime(end_date, "%Y-%m-%d").date()
        elif isinstance(end_date, datetime):
            ed = end_date.date()
        else:
            ed = end_date
        end_dt = datetime(ed.year, ed.month, ed.day, 23, 59, 59, 999999)

    return start_dt, end_dt


def get_revenue_report_data(start_date=None, end_date=None, cinema_id=None, movie_id=None):
    """
    Truy vấn tổng hợp doanh thu theo các bộ lọc:
    - start_date, end_date (lọc theo ngày chiếu của suất chiếu)
    - cinema_id (lọc theo rạp)
    - movie_id (lọc theo phim)
    """
    start_dt, end_dt = _build_date_range(start_date, end_date)

    # Base query kết hợp Ticket, Order, Showtime, Room, Cinema, Movie
    base_query = db.session.query(Ticket).join(Order, Ticket.order_id == Order.order_id)\
        .join(Showtime, Ticket.showtime_id == Showtime.showtime_id)\
        .join(Room, Showtime.room_id == Room.room_id)\
        .join(Cinema, Room.cinema_id == Cinema.cinema_id)\
        .filter(func.lower(Order.status) == 'success')\
        .filter(func.lower(func.coalesce(Ticket.status, '')) != 'cancelled')

    # Áp dụng các bộ lọc
    if start_dt:
        base_query = base_query.filter(Showtime.start_time >= start_dt)
    if end_dt:
        base_query = base_query.filter(Showtime.start_time <= end_dt)
    if cinema_id:
        base_query = base_query.filter(Room.cinema_id == cinema_id)
    if movie_id:
        base_query = base_query.filter(Showtime.movie_id == movie_id)

    # 1. Tính tổng doanh thu và số vé bán ra
    summary_row = base_query.with_entities(
        func.coalesce(func.sum(Ticket.ticket_price), 0).label('total_revenue'),
        func.count(Ticket.ticket_id).label('total_tickets'),
        func.count(distinct(Order.order_id)).label('total_orders')
    ).first()

    total_revenue = float(summary_row.total_revenue) if summary_row else 0.0
    total_tickets = int(summary_row.total_tickets) if summary_row else 0
    total_orders = int(summary_row.total_orders) if summary_row else 0

    # 2. Phân tích doanh thu theo từng ngày
    date_label = func.date(Showtime.start_time)
    daily_rows = base_query.with_entities(
        date_label.label('show_date'),
        func.coalesce(func.sum(Ticket.ticket_price), 0).label('daily_revenue'),
        func.count(Ticket.ticket_id).label('tickets_sold'),
        func.count(distinct(Order.order_id)).label('orders_count')
    ).group_by(date_label).order_by(date_label.asc()).all()

    daily_breakdown = []
    for r in daily_rows:
        d_str = r.show_date.strftime("%Y-%m-%d") if hasattr(r.show_date, 'strftime') else str(r.show_date)
        daily_breakdown.append({
            "date": d_str,
            "revenue": float(r.daily_revenue),
            "tickets_sold": int(r.tickets_sold),
            "orders_count": int(r.orders_count)
        })

    # 3. Phân tích doanh thu theo rạp
    cinema_rows = base_query.with_entities(
        Cinema.cinema_id,
        Cinema.name.label('cinema_name'),
        func.coalesce(func.sum(Ticket.ticket_price), 0).label('cinema_revenue'),
        func.count(Ticket.ticket_id).label('tickets_sold')
    ).group_by(Cinema.cinema_id, Cinema.name).order_by(desc('cinema_revenue')).all()

    cinema_breakdown = [
        {
            "cinema_id": c.cinema_id,
            "cinema_name": c.cinema_name,
            "revenue": float(c.cinema_revenue),
            "tickets_sold": int(c.tickets_sold)
        }
        for c in cinema_rows
    ]

    return {
        "total_revenue": total_revenue,
        "total_tickets_sold": total_tickets,
        "total_orders": total_orders,
        "daily_breakdown": daily_breakdown,
        "cinema_breakdown": cinema_breakdown
    }


def get_top_movies_report_data(start_date=None, end_date=None, limit=10):
    """
    Báo cáo hiệu suất phim: Top phim bán chạy nhất và đạt doanh thu cao nhất.
    """
    start_dt, end_dt = _build_date_range(start_date, end_date)

    query = db.session.query(
        Movie.movie_id,
        Movie.title,
        Movie.poster_url,
        Movie.duration_minutes,
        Movie.age_rating,
        func.coalesce(func.sum(Ticket.ticket_price), 0).label('total_revenue'),
        func.count(Ticket.ticket_id).label('total_tickets_sold'),
        func.count(distinct(Showtime.showtime_id)).label('total_showtimes')
    ).join(Showtime, Movie.movie_id == Showtime.movie_id)\
     .outerjoin(Ticket, (Showtime.showtime_id == Ticket.showtime_id) & (func.lower(func.coalesce(Ticket.status, '')) != 'cancelled'))\
     .outerjoin(Order, (Ticket.order_id == Order.order_id) & (func.lower(Order.status) == 'success'))

    if start_dt:
        query = query.filter(Showtime.start_time >= start_dt)
    if end_dt:
        query = query.filter(Showtime.start_time <= end_dt)

    rows = query.group_by(
        Movie.movie_id,
        Movie.title,
        Movie.poster_url,
        Movie.duration_minutes,
        Movie.age_rating
    ).order_by(desc('total_revenue'), desc('total_tickets_sold')).limit(limit).all()

    return [
        {
            "movie_id": r.movie_id,
            "title": r.title,
            "poster_url": r.poster_url,
            "duration_minutes": r.duration_minutes,
            "age_rating": r.age_rating,
            "total_revenue": float(r.total_revenue),
            "total_tickets_sold": int(r.total_tickets_sold),
            "total_showtimes": int(r.total_showtimes)
        }
        for r in rows
    ]


def get_overview_report_data():
    """
    Lấy dữ liệu tổng quan toàn hệ thống (Dashboard Overview cho Admin):
    - Tổng doanh thu toàn thời gian
    - Tổng số vé đã bán thành công
    - Tổng số đơn hàng thành công
    - Tổng số khách hàng
    - Tổng số phim đang có
    - Tổng số cụm rạp
    - 5 đơn hàng thành công gần nhất
    """
    # 1. Tổng doanh thu & đơn hàng
    order_stats = db.session.query(
        func.coalesce(func.sum(Order.total_amount), 0).label('revenue'),
        func.count(Order.order_id).label('order_count')
    ).filter(func.lower(Order.status) == 'success').first()

    total_revenue = float(order_stats.revenue) if order_stats else 0.0
    total_orders = int(order_stats.order_count) if order_stats else 0

    # 2. Tổng số vé bán thành công
    ticket_count = db.session.query(func.count(Ticket.ticket_id))\
        .join(Order, Ticket.order_id == Order.order_id)\
        .filter(func.lower(Order.status) == 'success')\
        .filter(func.lower(func.coalesce(Ticket.status, '')) != 'cancelled')\
        .scalar() or 0

    # 3. Đếm số khách hàng, phim, rạp
    user_count = User.query.filter(func.lower(func.coalesce(User.role, 'customer')) == 'customer').count()
    movie_count = Movie.query.count()
    cinema_count = Cinema.query.count()

    # 4. 5 đơn hàng gần nhất
    recent_orders_query = db.session.query(Order, User)\
        .outerjoin(User, Order.user_id == User.user_id)\
        .filter(func.lower(Order.status) == 'success')\
        .order_by(Order.order_id.desc())\
        .limit(5).all()

    recent_orders = [
        {
            "order_id": o.order_id,
            "user_id": o.user_id,
            "customer_name": u.name if u else "Unknown",
            "total_amount": float(o.total_amount),
            "status": o.status
        }
        for o, u in recent_orders_query
    ]

    return {
        "total_revenue": total_revenue,
        "total_tickets_sold": int(ticket_count),
        "total_orders": total_orders,
        "total_customers": user_count,
        "total_movies": movie_count,
        "total_cinemas": cinema_count,
        "recent_orders": recent_orders
    }


def get_cinema_performance_data(start_date=None, end_date=None):
    """
    Báo cáo hiệu suất theo từng rạp: Doanh thu, số vé, số phòng chiếu, số suất chiếu.
    """
    start_dt, end_dt = _build_date_range(start_date, end_date)

    cinemas = Cinema.query.all()
    results = []

    for cinema in cinemas:
        # Lấy danh sách room_ids
        room_ids = [room.room_id for room in cinema.rooms]
        total_rooms = len(room_ids)

        if not room_ids:
            results.append({
                "cinema_id": cinema.cinema_id,
                "cinema_name": cinema.name,
                "address": cinema.address,
                "total_rooms": 0,
                "total_showtimes": 0,
                "tickets_sold": 0,
                "revenue": 0.0
            })
            continue

        st_query = Showtime.query.filter(Showtime.room_id.in_(room_ids))
        if start_dt:
            st_query = st_query.filter(Showtime.start_time >= start_dt)
        if end_dt:
            st_query = st_query.filter(Showtime.start_time <= end_dt)

        total_showtimes = st_query.count()
        showtime_ids = [st.showtime_id for st in st_query.all()]

        if not showtime_ids:
            results.append({
                "cinema_id": cinema.cinema_id,
                "cinema_name": cinema.name,
                "address": cinema.address,
                "total_rooms": total_rooms,
                "total_showtimes": 0,
                "tickets_sold": 0,
                "revenue": 0.0
            })
            continue

        ticket_stats = db.session.query(
            func.coalesce(func.sum(Ticket.ticket_price), 0).label('revenue'),
            func.count(Ticket.ticket_id).label('tickets_sold')
        ).join(Order, Ticket.order_id == Order.order_id)\
         .filter(Ticket.showtime_id.in_(showtime_ids))\
         .filter(func.lower(Order.status) == 'success')\
         .filter(func.lower(func.coalesce(Ticket.status, '')) != 'cancelled')\
         .first()

        revenue = float(ticket_stats.revenue) if ticket_stats else 0.0
        tickets_sold = int(ticket_stats.tickets_sold) if ticket_stats else 0

        results.append({
            "cinema_id": cinema.cinema_id,
            "cinema_name": cinema.name,
            "address": cinema.address,
            "total_rooms": total_rooms,
            "total_showtimes": total_showtimes,
            "tickets_sold": tickets_sold,
            "revenue": revenue
        })

    # Sắp xếp theo doanh thu giảm dần
    results.sort(key=lambda x: x["revenue"], reverse=True)
    return results
