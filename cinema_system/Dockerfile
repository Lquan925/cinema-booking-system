# Sử dụng image Python 3.11 bản rút gọn (nhẹ, bảo mật, tối ưu)
FROM python:3.11-slim

# Ngăn Python tạo file .pyc và hiển thị log trực tiếp ra console
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Cài đặt các thư viện phụ thuộc của hệ thống (nếu có yêu cầu từ cryptography)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt trước để tận dụng Docker layer caching
COPY requirements.txt .

# Cài đặt các thư viện Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn dự án vào container
COPY . .

# Mở cổng 5000 cho ứng dụng Flask
EXPOSE 5000

# Khởi chạy ứng dụng
CMD ["python", "run.py"]
