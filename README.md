# Cinema Booking System

## ⚙️ Cấu hình file `.env`

Tạo file `.env` bên trong thư mục `cinema_system/` bằng cách sao chép từ file mẫu `.env.example`:

- **Windows (PowerShell):**
  ```powershell
  cd cinema_system
  Copy-Item .env.example .env
  ```
- **Linux / macOS / Git Bash:**
  ```bash
  cd cinema_system
  cp .env.example .env
  ```

### Mẫu nội dung file `.env` (`cinema_system/.env`):

```env
# 1. Cấu hình kết nối MySQL (Cổng 3307 được ánh xạ từ Docker Compose)
SQLALCHEMY_DATABASE_URI=mysql+pymysql://cinema_user:cinema_password@localhost:3307/cinema_db
SQLALCHEMY_TRACK_MODIFICATIONS=False

# 2. Cấu hình kết nối Redis (Cache & giữ ghế realtime)
REDIS_URL=redis://localhost:6379/0

# 3. Khóa bí mật cho Flask (Session, token bảo mật)
SECRET_KEY=super-secret-key-cinema-2026
```

### Ý nghĩa các biến môi trường:

- `SQLALCHEMY_DATABASE_URI`: Chuỗi kết nối MySQL với định dạng `mysql+pymysql://<user>:<password>@<host>:<port>/<db_name>`. Dùng cổng `3307` tương ứng với cổng host trong `docker-compose.yml`.
- `SQLALCHEMY_TRACK_MODIFICATIONS`: Đặt `False` để tắt cảnh báo và tối ưu bộ nhớ.
- `REDIS_URL`: Chuỗi kết nối tới Redis (`redis://localhost:6379/0`) để quản lý cache và giữ ghế realtime.
- `SECRET_KEY`: Khóa bí mật dùng cho ứng dụng Flask để mã hóa session/cookie.

> **Lưu ý**: File `.env` chứa mật khẩu thực tế nên đã được thêm vào `.gitignore` để không bị đẩy lên Git.
