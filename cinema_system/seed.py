from app import create_app, db
from app.models import User, Cinema, Room, Seat, Movie, Showtime, Order, Ticket
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

# Khởi tạo app để lấy ngữ cảnh (context) kết nối database
app = create_app()

with app.app_context():
    print("Đang dọn dẹp dữ liệu cũ...")
    db.drop_all()   # Xóa toàn bộ bảng cũ (nếu có)
    db.create_all() # Tạo lại bảng mới cứng

    print("Đang tạo Users...")
    admin = User(name="Admin System", email="admin@cinema.com", password=generate_password_hash("123456"), role="admin")
    customer = User(name="Khách Hàng A", email="khachhang@gmail.com", password=generate_password_hash("123456"), role="customer")
    db.session.add_all([admin, customer])
    db.session.commit()

    print("Đang tạo Cinemas và Rooms...")
    cinema1 = Cinema(name="CGV Vincom Center", address="Hà Nội", hotline="19001234")
    db.session.add(cinema1)
    db.session.commit()

    room1 = Room(name="Phòng 1 - IMAX", screen_type="IMAX", cinema_id=cinema1.cinema_id)
    db.session.add(room1)
    db.session.commit()

    print("Đang tạo sơ đồ Seats (2 hàng, mỗi hàng 5 ghế)...")
    seats = []
    for row in ['A', 'B']:
        for num in range(1, 6):
            seat = Seat(seat_row=row, seat_number=num, seat_type="Normal", room_id=room1.room_id)
            seats.append(seat)
    db.session.add_all(seats)
    db.session.commit()

    print("Đang tạo Movies...")
    movie1 = Movie(
        title="Attack on Titan: The Roar of Awakening",
        description="Trận chiến sinh tồn của nhân loại trước các Titan.",
        duration_minutes=120,
        age_rating="16+",
        poster_url="https://dummyimage.com/600x800/000/fff&text=AOT",
        trailer_url="https://youtube.com/..."
    )
    movie2 = Movie(
        title="Oppenheimer",
        description="Cha đẻ bom nguyên tử.",
        duration_minutes=180,
        age_rating="18+",
        poster_url="https://dummyimage.com/600x800/000/fff&text=Oppenheimer",
        trailer_url="https://youtube.com/..."
    )
    db.session.add_all([movie1, movie2])
    db.session.commit()

    print("Đang tạo Showtimes...")
    now = datetime.now()
    showtime1 = Showtime(
        movie_id=movie1.movie_id,
        room_id=room1.room_id,
        start_time=now + timedelta(days=1),
        end_time=now + timedelta(days=1, hours=2),
        price=100000
    )
    db.session.add(showtime1)
    db.session.commit()

    print("Đang tạo Orders và Tickets (Giả lập khách đã mua vé)...")
    # Khách hàng mua 2 vé (Ghế A1 và A2)
    order1 = Order(user_id=customer.user_id, total_amount=200000, status="paid")
    db.session.add(order1)
    db.session.commit()

    ticket1 = Ticket(
        ticket_price=100000, qr_code_url="qr_mock_1", status="active",
        order_id=order1.order_id, showtime_id=showtime1.showtime_id, seat_id=seats[0].seat_id # Ghế A1
    )
    ticket2 = Ticket(
        ticket_price=100000, qr_code_url="qr_mock_2", status="active",
        order_id=order1.order_id, showtime_id=showtime1.showtime_id, seat_id=seats[1].seat_id # Ghế A2
    )
    db.session.add_all([ticket1, ticket2])
    db.session.commit()

    print("✅ Bơm dữ liệu (Seeding) hoàn tất!")