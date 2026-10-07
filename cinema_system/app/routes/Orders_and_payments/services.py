"""
Orders & Payments – Business Logic Layer (Services)
=====================================================
Xử lý nghiệp vụ đơn hàng và thanh toán.
Truy cập dữ liệu thông qua repositories (Data Access Layer).
"""
import uuid
from app.repositories import booking_repository, user_repository


def get_total_amount(tickets):
    """Tính tổng tiền từ danh sách vé"""
    total_amount = 0
    for ticket in tickets:
        total_amount += ticket.ticket_price
    return total_amount


def create_order(user_id, ticket_ids):
    """
    Tạo đơn hàng mới từ danh sách ticket_ids:
    - Lấy danh sách vé từ repository
    - Tính tổng tiền
    - Tạo order và gắn vé vào order
    """
    tickets = booking_repository.get_tickets_by_ids(ticket_ids)
    if not tickets:
        return None, "Không tìm thấy vé nào!"

    total_amount = get_total_amount(tickets)

    order, error = booking_repository.create_order(user_id, total_amount, status='pending')
    if error:
        return None, f"Lỗi khi tạo đơn hàng: {error}"

    # Gắn vé vào đơn hàng
    for ticket in tickets:
        booking_repository.update_ticket(ticket, order_id=order.order_id, status='pending')

    booking_repository.commit()
    return order, None


def process_payment(order_id):
    """
    Xử lý thanh toán cho đơn hàng:
    - Kiểm tra order tồn tại
    - Kiểm tra số dư ví người dùng
    - Trừ tiền, cộng điểm, cập nhật trạng thái
    """
    order = booking_repository.get_order_by_id(order_id)
    if not order:
        return None, "Order not found"

    user = user_repository.get_by_id(order.user_id)
    if not user:
        return None, "User not found"

    if user.wallet_balance < order.total_amount:
        return None, "Insufficient balance"

    # Cập nhật số dư và điểm thưởng
    user_repository.update(user,
        loyalty_points=user.loyalty_points + 1,
        wallet_balance=user.wallet_balance - order.total_amount
    )

    # Cập nhật trạng thái order
    booking_repository.update_order(order, status='success')

    # Cập nhật trạng thái vé và tạo QR code
    tickets = booking_repository.get_tickets_by_order(order_id)
    for ticket in tickets:
        booking_repository.update_ticket(
            ticket,
            status='ready',
            qr_code_url=f"https://example.com/qr/{uuid.uuid4()}"
        )

    return order, None


def get_order_history(user_id):
    """Lấy lịch sử đơn hàng của người dùng qua repository"""
    orders = booking_repository.get_orders_by_user(user_id)
    return [
        {
            "user_id": o.user_id,
            "order_id": o.order_id,
            "total_amount": float(o.total_amount),
            "status": o.status
        }
        for o in orders
    ]

