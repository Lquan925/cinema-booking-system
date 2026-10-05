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
    customer1 = User(
            name="Khách test An",
            email="test01@example.com",
            password=generate_password_hash("123456"),
            role="customer",
            loyalty_points=20,
            wallet_balance=300000
        )
    
    customer2 = User(
            name="Khách test Bình",
            email="test02@example.com",
            password=generate_password_hash("123456"),
            role="customer",
            loyalty_points=10,
            wallet_balance=150000
        )
    
    customer3 = User(
            name="Khách test Chi",
            email="test03@example.com",
            password=generate_password_hash("123456"),
            role="customer",
            loyalty_points=0,
            wallet_balance=0
        )
    
    customer4 = User(
            name="Khách test Dũng",
            email="test04@example.com",
            password=generate_password_hash("123456"),
            role="customer",
            loyalty_points=0,
            wallet_balance=30000
        )
    
    staff = User(
            name="Nhân viên test",
            email="test05@example.com",
            password=generate_password_hash("123456"),
            role="staff",
            loyalty_points=0,
            wallet_balance=0
        )
    
    admin = User(
            name="Quản trị test",
            email="test06@example.com",
            password=generate_password_hash("123456"),
            role="admin",
            loyalty_points=0,
            wallet_balance=0
        )
    db.session.add_all([
        customer1, customer2, customer3, customer4, staff, admin
    ])
    db.session.commit()

    print("Đang tạo Cinemas và Rooms...")
    cinema1 = Cinema(
        name="Beta Cinemas Mỹ Đình",
        address="Tầng hầm B1, tòa nhà Golden Palace, đường Mễ Trì, Hà Nội",
        hotline="0866154610"
    )
    db.session.add(cinema1)
    db.session.commit()

    room1 = Room(
        name="Phòng test 1",
        screen_type="2D",
        cinema_id=cinema1.cinema_id
    )

    room2 = Room(
        name="Phòng test 2",
        screen_type="2D",
        cinema_id=cinema1.cinema_id
    )
    
    db.session.add(room1)
    db.session.add(room2)
    db.session.commit()

    print("Đang tạo sơ đồ Seats (4 hàng, mỗi hàng 6 ghế)...")
    seats = []
    for room in [room1, room2]:
        for row in ['A', 'B', 'C', 'D']:
            for num in range(1, 7):

                seat = Seat(
                    seat_row=row,
                    seat_number=num,
                    seat_type="VIP" if row in ['B', 'C'] else "NORMAL",
                    room_id=room.room_id
                )

                seats.append(seat)

    db.session.add_all(seats)
    db.session.commit()

    print("Đang tạo Movies...")
    movie1 = Movie(
        title="Mai",
        description="Một người phụ nữ từng trải đối diện tình yêu và những tổn thương trong quá khứ.",
        duration_minutes=131,
        age_rating="18+",
        poster_url="https://dummyimage.com/600x800/000/fff&text=Mai",
        trailer_url="https://youtu.be/EX6clvId19s?si=b_6CRmRPJXvsuzHt"
    )
    movie2 = Movie(
        title="Đào, Phở và Piano",
        description="Câu chuyện tình yêu và cuộc sống của người Hà Nội trong những ngày chiến đấu bảo vệ Thủ đô.",
        duration_minutes=100,
        age_rating="13+",
        poster_url="https://dummyimage.com/600x800/000/fff&text=Đào%2C%20Phở%20và%20Piano",
        trailer_url="https://youtu.be/qn1t_biQigc?si=foBSwfQ9TdshCa43"
    )
    db.session.add_all([movie1, movie2])
    db.session.commit()

    print("Đang tạo Showtimes...")
    now = datetime.now()

    # (movie, room, ngày cộng thêm, giờ cộng thêm, giá)
    showtime_data = [
        (movie1, room1, 1, 0, 60000),
        (movie2, room1, 1, 3, 55000),
        (movie2, room2, 1, 0, 65000),
        (movie1, room1, 2, 0, 70000),
        (movie2, room1, 2, 3, 65000),
        (movie2, room2, 2, 0, 70000)
    ]

    showtimes = []

    for movie, room, day, hour, price in showtime_data:
        showtime = Showtime(
            movie_id=movie.movie_id,
            room_id=room.room_id,
            start_time=now + timedelta(days=day),
            end_time=now + timedelta(minutes=movie.duration_minutes),
            price=price
        )
        showtimes.append(showtime)

    db.session.add_all(showtimes)
    db.session.commit()

    showtime1, showtime2, showtime3, showtime4, showtime5, showtime6 = showtimes

    print("Đang tạo Orders và Tickets (Giả lập khách đã mua vé)...")
    # Khách hàng mua 2 vé (Ghế A1 và A2)
    order1 = Order(
        user_id=customer1.user_id,
        total_amount=120000,
        status="SUCCESS"
    )

    order2 = Order(
        user_id=customer2.user_id,
        total_amount=70000,
        status="SUCCESS"
    )

    order3 = Order(
        user_id=customer3.user_id,
        total_amount=55000,
        status="PENDING"
    )

    order4 = Order(
        user_id=customer4.user_id,
        total_amount=55000,
        status="FAILED"
    )

    order5 = Order(
        user_id=customer1.user_id,
        total_amount=70000,
        status="REFUNDED"
    )

    order6 = Order(
        user_id=customer2.user_id,
        total_amount=70000,
        status="SUCCESS"
    )
    db.session.add_all([order1, order2, order3, order4, order5, order6])
    db.session.commit()

    print("Đang tạo Tickets...")
    ticket1 = Ticket(
        ticket_price=60000, qr_code_url="qr_mock_1", status="UNUSED",
        order_id=order1.order_id, showtime_id=showtime1.showtime_id,
        seat_id=seats[6].seat_id  # Phòng 1 - Ghế B01
    )

    ticket2 = Ticket(
        ticket_price=60000, qr_code_url="qr_mock_2", status="UNUSED",
        order_id=order1.order_id, showtime_id=showtime1.showtime_id,
        seat_id=seats[7].seat_id  # Phòng 1 - Ghế B02
    )

    ticket3 = Ticket(
        ticket_price=70000, qr_code_url="qr_mock_3", status="CHECKED_IN",
        order_id=order2.order_id, showtime_id=showtime3.showtime_id,
        seat_id=seats[30].seat_id  # Phòng 2 - Ghế B01
    )

    ticket4 = Ticket(
        ticket_price=70000, qr_code_url="qr_mock_4", status="CANCELLED",
        order_id=order5.order_id, showtime_id=showtime3.showtime_id,
        seat_id=seats[31].seat_id  # Phòng 2 - Ghế B02
    )

    ticket5 = Ticket(
        ticket_price=70000, qr_code_url="qr_mock_5", status="UNUSED",
        order_id=order6.order_id, showtime_id=showtime3.showtime_id,
        seat_id=seats[31].seat_id  # Phòng 2 - Ghế B02 (mua lại sau khi hủy)
    )

    db.session.add_all([ticket1, ticket2, ticket3, ticket4, ticket5])
    db.session.commit()

    print("\n===== DATABASE SUMMARY =====")
    print("Users:", User.query.count())
    print("Cinemas:", Cinema.query.count())
    print("Rooms:", Room.query.count())
    print("Seats:", Seat.query.count())
    print("Movies:", Movie.query.count())
    print("Showtimes:", Showtime.query.count())
    print("Orders:", Order.query.count())
    print("Tickets:", Ticket.query.count())
    
    print("✅ Bơm dữ liệu (Seeding) hoàn tất!")