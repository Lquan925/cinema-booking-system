import os
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Biến kết nối dùng chung cho nhánh của Quân
redis_db = redis.from_url(REDIS_URL, decode_responses=True)

# Hàm Singleton dùng cho nhánh Booking của Mạnh
_redis_client = None

def get_redis_client():
    """
    Khởi tạo hoặc trả về kết nối Redis client dạng Singleton.
    Sử dụng decode_responses=True để tự động chuyển kết quả từ bytes sang chuỗi str.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3
        )
    return _redis_client

def set_redis_client(client):
    """
    Hỗ trợ gán client tùy chỉnh (ví dụ fakeredis trong unit test hoặc mock).
    """
    global _redis_client
    _redis_client = client
