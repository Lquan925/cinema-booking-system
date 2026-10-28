# Báo cáo dự án Cinema Booking System

## 1. Tóm tắt dự án

Cinema Booking System là backend REST API cho nghiệp vụ đặt vé xem phim:

- Quản lý người dùng, đăng nhập, ví điện tử và điểm tích lũy.
- Quản lý phim, rạp, phòng chiếu, ghế và lịch chiếu.
- Giữ ghế tạm thời bằng Redis để chống double-booking.
- Tạo đơn hàng, thanh toán bằng ví, sinh mã QR cho vé.
- Báo cáo doanh thu và hiệu suất bán vé cho admin.

## 2. Công nghệ sử dụng

| Thành phần | Công nghệ | Ghi chú |
| :--- | :--- | :--- |
| Ngôn ngữ | Python 3.9+ | Docker dùng `python:3.11-slim` |
| Web framework | Flask | Blueprint theo module |
| ORM | Flask-SQLAlchemy | Model trong `app/models.py` |
| Migration | Flask-Migrate / Alembic | Migration hiện chưa đầy đủ |
| Database | MySQL 8.0 | Chạy trong Docker, host port `3307` |
| Cache / lock | Redis 7 | Giữ ghế tạm thời, TTL |
| DB GUI | Adminer | Chỉ dùng khi phát triển |
| Token | itsdangerous `URLSafeTimedSerializer` | Token có hạn 24 giờ |
| Hash mật khẩu | `werkzeug.security` | scrypt/pbkdf2 |
| Đóng gói | Docker, Docker Compose | Có Dockerfile và compose |
| Tài liệu API | OpenAPI 3.0.3 + Swagger UI | 5 file YAML trong `cinema_system/API spec/` |

## 3. Kiến trúc và luồng request

### 3.1 Kiến trúc

```text
Client (Web / Mobile / Postman)
            │
            ▼
┌──────────────────────────────────────────────┐
│  Auth Middleware (app/middleware/auth.py)    │
│  - Xác thực Token tập trung (before_request) │
│  - Phân quyền (Role: CUSTOMER, STAFF, ADMIN) │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  Routes Layer (Blueprints)                   │
│  - Nhận HTTP Request, parse & validate input │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  Services Layer                              │
│  - Xử lý Business Logic, tính tiền, ví ảo   │
│  - Điều phối khóa ghế Redis (TTL 5 - 10 phút)│
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│  Repositories Layer                          │
│  - Tách biệt truy vấn dữ liệu (DB/Cache)    │
└──────────────┬───────────────────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌──────────────┐ ┌──────────────┐
│ MySQL DB 8.0 │ │ Redis Cache  │
│ (Persistent) │ │ (Seat Locks) │
└──────────────┘ └──────────────┘
```

### 3.2 Chức năng của các tầng

| Tầng | Chức năng |
| :--- | :--- |
| Middleware | Xác thực token, gán `g.current_user`, chặn admin cho `/api/admin/*` |
| Routes | Chuyển HTTP ↔ service, validate input cơ bản, map lỗi |
| Services | Nghiệp vụ, kiểm tra quy tắc, điều phối repository |
| Repositories | Truy vấn/ghi MySQL hoặc Redis |
| Models | Định nghĩa bảng và quan hệ |

### 3.3 Luồng request điển hình

1. Client gửi request tới Flask.
2. `authenticate()` trong `before_request` kiểm tra endpoint public hay cần token.
3. Token hợp lệ → middleware gán `g.current_user`.
4. Blueprint tương ứng nhận request, parse JSON/query params.
5. Route gọi service.
6. Service gọi một hoặc nhiều repository.
7. Repository đọc/ghi MySQL hoặc Redis.
8. Route trả JSON + HTTP status.

## 4. Cấu trúc thư mục

```text
cinema-booking-system/
├── README.md                       # Giới thiệu, kiến trúc tổng quan, hướng dẫn chạy
├── TECHNICAL.md                    # Tài liệu kỹ thuật bàn giao Phase 2
├── .gitignore
└── cinema_system/
    ├── app/
    │   ├── __init__.py             # create_app, db, migrate, đăng ký blueprint
    │   ├── docs.py                 # Swagger UI + serve file OpenAPI
    │   ├── models.py               # 8 SQLAlchemy models
    │   ├── redis_client.py         # Singleton Redis client
    │   ├── security.py             # Sinh token đăng nhập
    │   ├── middleware/
    │   │   └── auth.py             # Xác thực/phân quyền tập trung
    │   ├── repositories/
    │   │   ├── booking_repository.py
    │   │   ├── user_repository.py
    │   │   ├── analytics_repository.py
    │   │   └── seat_lock_repository.py
    │   └── routes/
    │       ├── User_management/    # register, login, profile, admin users
    │       ├── Catalog_and_showtime/ # movies, cinemas, showtimes
    │       ├── Booking_and_seat/   # seat map, lock/unlock
    │       ├── Orders_and_payments/# orders, payment, history
    │       └── Reports_and_Analytics/ # admin reports
    ├── API spec/                   # 5 file OpenAPI YAML
    ├── migrations/                 # Alembic; hiện chỉ có migration Users/Cinemas
    ├── tests/
    │   └── test_booking_seats.py   # 8 test ghế; đang bị .gitignore loại bỏ
    ├── Dockerfile
    ├── docker-compose.yml
    ├── seed.py                     # db.drop_all + db.create_all + dữ liệu mẫu
    ├── requirements.txt
    ├── run.py                      # Flask dev server, debug=True
    └── .env.example
```

> `tests/` đang bị `.gitignore` loại trừ nên không có trong repo public. Đây là lỗi cần sửa ở Phase 2.

## 5. Mô hình dữ liệu

![Sơ đồ quan hệ thực thể (ERD)](https://media.discordapp.net/attachments/1216040842213589033/1565028587441098792/image.png?ex=6ae369f4&is=6ae21874&hm=2ad7c62aa9b7aded27a32e87c065d8536b7a21ed53ea88ba1f5a9cbc46d077fb&=&format=webp&quality=lossless)

<!-- Dán link ảnh ERD vào PASTE_IMAGE_URL_ERD -->

## 6. API và Swagger

### 6.1 Danh sách endpoint

| Method | Path | Xác thực | Quyền | Ghi chú |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/auth/register` | Public | — | Đăng ký customer |
| POST | `/api/auth/login` | Public | — | Trả token + user |
| GET | `/api/users/profile` | Token | User | Thông tin cá nhân |
| PUT | `/api/users/profile` | Token | User | Đổi tên/mật khẩu |
| GET | `/api/admin/users` | Token | Admin | Danh sách user, có filter/phân trang |
| POST | `/api/admin/users` | Token | Admin | Tạo staff/admin |
| DELETE | `/api/admin/users/<user_id>` | Token | Admin | Xóa user |
| GET | `/api/movies` | Public | — | Danh sách phim |
| GET | `/api/cinemas` | Public | — | Danh sách rạp |
| GET | `/api/showtimes` | Public | — | Lọc `date`, `movie_id`, `cinema_id` |
| POST | `/api/movies` | Token | Admin* | *Route tự kiểm tra role |
| POST | `/api/showtimes` | Token | Admin* | *Route tự kiểm tra role |
| DELETE | `/api/showtimes/<id>` | Token | Admin* | *Route tự kiểm tra role |
| GET | `/api/showtimes/<id>/seats` | Public | — | Sơ đồ ghế + trạng thái realtime |
| POST | `/api/booking/lock-seat` | Token | User | Khóa 1/nhiều ghế |
| POST | `/api/booking/unlock-seat` | Token | User | Mở khóa ghế |
| POST | `/api/orders` | Token | User | Tạo order từ `ticket_ids` |
| POST | `/api/payments/process/<order_id>` | Token | User | Thanh toán bằng ví |
| GET | `/api/orders/history` | Token | User | Lịch sử order |
| GET | `/api/admin/reports/revenue` | Token | Admin | Báo cáo doanh thu |
| GET | `/api/admin/reports/movies` | Token | Admin | Top phim |
| GET | `/api/admin/reports/overview` | Token | Admin | Dashboard |
| GET | `/api/admin/reports/cinemas` | Token | Admin | Hiệu suất rạp |

## 7. Xác thực và phân quyền

```text
POST /api/auth/login
 → User_management/services.authenticate_user(email, password)
 → user_repository.get_by_email
 → so khớp password hash
 → security.generate_token(user_id, role, SECRET_KEY)
 → trả {"token": "...", "user": {...}}
```

### 7.1 Luồng đăng nhập

Token là chuỗi ký bằng `itsdangerous.URLSafeTimedSerializer`, payload gồm `user_id` và `role`, hạn `86400` giây (24 giờ).

### 7.2 Middleware

`app/middleware/auth.py` đăng ký `@app.before_request`:

1. Nếu endpoint public: cho qua; nếu có token thì cố gắn `g.current_user`.
2. Trích token từ `Authorization: Bearer`, `x-access-token`.
3. Nếu không có token: kiểm tra header `X-User-Id` (dev fallback).
4. Giải mã token, lấy user từ DB; không hợp lệ → 401.
5. Nếu path bắt đầu bằng `/api/admin/` và role không phải admin → 403.
6. Gán `g.current_user` và cho qua.

### 7.3 Phân quyền admin

- Nhóm `/api/admin/*`: middleware tự kiểm tra role.
- `POST /api/movies`, `POST /api/showtimes`, `DELETE /api/showtimes/<id>`: route tự kiểm tra role (lặp code).

## 8. Giữ ghế, đơn hàng và thanh toán

### 8.1 Redis key

| Key | Kiểu | Giá trị | TTL |
| :--- | :--- | :--- | :--- |
| `seat_lock:{showtime_id}:{seat_id}` | string | `user_id` đang giữ | 600 giây mặc định |
| `user_locks:{user_id}:{showtime_id}` | set | danh sách `seat_id` user đang giữ | được expire theo TTL |

### 8.2 Thuật toán lock ghế

`POST /api/booking/lock-seat`:

1. Validate `showtime_id`, `seat_ids`; loại bỏ trùng.
2. Kiểm tra user và showtime tồn tại.
3. Kiểm tra toàn bộ ghế thuộc phòng của showtime.
4. Kiểm tra ghế đã có ticket chưa hủy chưa.
5. Đồng bộ danh sách ghế user đang giữ; giới hạn tối đa 8 ghế/user/showtime.
6. Với từng ghế: `SET seat_lock:... user_id NX EX ttl`.
7. Nếu một ghế bị người khác giữ → rollback các ghế vừa khóa trong batch, trả 409.
8. Thành công → cập nhật set `user_locks`, trả danh sách ghế + TTL.

`POST /api/booking/unlock-seat`:

- Có `seat_id`/`seat_ids`: chỉ mở khóa ghế thuộc user hiện tại; ghế của người khác → 403.
- Không truyền danh sách: mở khóa toàn bộ ghế user đang giữ cho showtime.

### 8.3 Trạng thái ghế trả về

`GET /api/showtimes/<id>/seats` trả:

- `sold`: đã có ticket không bị cancelled trong MySQL.
- `locked`: đang có key Redis.
- `available`: còn trống.
- Kèm `locked_by`, `is_my_lock`, `expires_in_seconds`.

Nếu Redis lỗi, service vẫn trả sơ đồ ghế và coi như không có lock tạm thời (degrade).

### 8.4 Luồng đặt vé hiện tại

```text
1. POST /api/auth/login
2. GET  /api/showtimes/{id}/seats
3. POST /api/booking/lock-seat          (Redis)
4. POST /api/orders {ticket_ids:[...]}  (MySQL)
5. POST /api/payments/process/{order_id}
```

### 8.5 Thanh toán hiện tại

`POST /api/payments/process/<order_id>`:

1. Tìm order; chỉ order `pending` mới thanh toán.
2. Lấy user từ `order.user_id`.
3. Kiểm tra ví đủ tiền.
4. `claim_order_for_payment` chuyển order → `success` nguyên tử.
5. Trừ ví + cộng 1 điểm loyalty nguyên tử.
6. Nếu trừ ví thất bại → revert order về `pending`.
7. Cập nhật ticket → `ready`, sinh `qr_code_url`.

## 9. Kiểm thử tải

![Bảng kết quả kiểm thử tải](https://media.discordapp.net/attachments/1216040842213589033/1565028622777983036/image.png?ex=6ae369fc&is=6ae2187c&hm=bf173a6817a7aac5184aaeb9984fcfb74ed2540725c32fd5b7c48638e41892e3&=&format=webp&quality=lossless&width=768&height=230)

<!-- Dán link ảnh kết quả load test vào PASTE_IMAGE_URL_LOAD_TEST -->

## 10. Cài đặt

### Chạy toàn bộ bằng Docker (khuyến nghị)

```bash
cd cinema_system
docker compose up -d --build
# Lần đầu: tạo bảng + nạp dữ liệu mẫu trong container
docker compose exec app python seed.py
```

Truy cập:

- API: `http://localhost:5000`
- Swagger UI: `http://localhost:5000/api/docs`

Kiểm tra:

```bash
docker compose ps
docker compose logs -f app
```

Dừng:

```bash
docker compose down          # giữ dữ liệu
docker compose down -v       # xóa luôn volume MySQL/Redis
```

> `seed.py` gọi `db.drop_all()` trước khi tạo dữ liệu. Không chạy trên môi trường có dữ liệu thật. Phase 2 nên tách script seed khỏi flow deploy và dùng migration cho production.

### Chạy app local, MySQL/Redis bằng Docker

```bash
cd cinema_system
# Nếu app container đang chạy, dừng để tránh chiếm cổng 5000
docker compose stop app
docker compose up -d mysql-db redis-cache adminer
python -m venv venv
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
# source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed.py
python run.py
```

`run.py` chạy Flask dev server tại `0.0.0.0:5000`, `debug=True`. Không dùng cấu hình này cho production.
