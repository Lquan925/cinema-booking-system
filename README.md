# Catalog & Showtimes

Module quản lý danh mục phim, rạp và suất chiếu cho Phase 1.

## Chức năng

| Method | Endpoint | Chức năng |
| --- | --- | --- |
| GET | /api/movies | Danh sách phim kèm thông tin phim |
| GET | /api/cinemas | Danh sách rạp |
| GET | /api/showtimes | Danh sách suất chiếu |
| POST | /api/admin/movies | Thêm phim |
| POST | /api/admin/showtimes | Tạo suất chiếu |
| DELETE | /api/admin/showtimes/{showtime_id} | Xóa suất chiếu chưa có vé liên quan |

Ảnh và trailer được lưu dưới dạng URL.

## Tổ chức mã nguồn

- `routes.py`: nhận request, gọi service và trả JSON cùng HTTP status.
- `services.py`: kiểm tra dữ liệu và chứa class `CatalogRepository`
  thực hiện truy vấn ORM. Có thể tách ở Services thành Repository thành file riêng.
- Blueprint `catalog_bp` được đăng ký trong `app/__init__`.

## Quy tắc xử lý

- Tên phim không được rỗng; thời lượng phải là số nguyên dương.
- Suất chiếu phải tham chiếu phim và phòng tồn tại.
- Giờ bắt đầu phải nằm trong tương lai.
- Giờ kết thúc được tính từ giờ bắt đầu và thời lượng phim.
- Không tạo lịch trùng trong cùng phòng.
- Giá vé không âm và tối đa hai chữ số thập phân.
- Không xóa suất chiếu đã có vé liên quan, kể cả vé đã hủy.

Thời gian input dùng giờ Việt Nam, không kèm offset,
ví dụ `2026-10-10T19:00:00`. Giá vé được trả dưới dạng chuỗi.

## Chạy trên máy

Từ thư mục gốc repository:

Mở Docker Desktop, khởi động MySQL:

Database cần có schema và dữ liệu thử trước khi kiểm tra API.
Không chạy seed có `drop_all()` trên database chung.

Khởi động Flask:

```powershell
python run.py
```

API chạy tại `http://127.0.0.1:5000`.

### API GET

Mở trực tiếp bằng trình duyệt:

- [Danh sách phim](http://127.0.0.1:5000/api/movies)
- [Danh sách rạp](http://127.0.0.1:5000/api/cinemas)
- [Danh sách suất chiếu](http://127.0.0.1:5000/api/showtimes)

Kết quả mong đợi: HTTP `200`, JSON dạng `{"data": [...]}`.

### API POST và DELETE

Dùng Postman hoặc PowerShell; mở URL trực tiếp trên trình duyệt sẽ gửi GET.

## Ví dụ tạo suất chiếu

```json
{
  "movie_id": 1,
  "room_id": 1,
  "start_time": "2026-10-10T19:00:00",
  "price": "70000.00"
}
```

Sử dụng ID thực tế và thời điểm tương lai chưa có lịch trùng.

## Phần chưa hoàn thiện

- Chưa tích hợp xác thực và phân quyền admin từ module User Management.
  Hiện các endpoint ghi chưa được bảo vệ.
- Chưa tách Repository khỏi file services để hoàn thiện kiến trúc **Layered Architecture**.
- Chưa bổ sung unit tests và đặc tả OpenAPI cho module.
- Cần thống nhất cơ chế khóa với module Booking để xử lý đặt vé đồng thời với xóa suất chiếu.

Các endpoint ghi hiện dùng để phát triển và kiểm thử cục bộ; chưa triển khai công khai trước khi tích hợp phân quyền.