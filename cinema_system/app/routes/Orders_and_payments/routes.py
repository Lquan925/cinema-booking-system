from flask import Blueprint, request, jsonify
from . import services

# Gắn tiền tố /api cho toàn bộ các route trong module này
orders_bp = Blueprint('orders_and_payments', __name__, url_prefix='/api')

@orders_bp.route('/orders', methods=['POST'])
def create_order():
    """
    API tạo đơn hàng mới.
    Request body (JSON): { "ticket_ids": [1, 2, 3] }
    """
    from flask import g
    
    data = request.get_json(silent=True) or {}
    ticket_ids = data.get("ticket_ids", [])

    if not ticket_ids:
        return jsonify({"message": "Vui lòng chọn ít nhất 1 vé!"}), 400

    # Lấy user_id từ Token bảo mật (đã được Auth Middleware kiểm chứng)
    user_id = g.current_user.user_id

    order, error = services.create_order(user_id, ticket_ids)
    if error:
        return jsonify({"message": error}), 400

    return jsonify({"message": "Order created successfully", "order_id": order.order_id}), 201


@orders_bp.route('/payments/process/<string:order_id>', methods=['POST'])
def process_payment(order_id):
    """API xử lý thanh toán cho đơn hàng"""
    order, error = services.process_payment(order_id)
    if error == "Order not found":
        return jsonify({"message": error}), 404
    if error == "User not found":
        return jsonify({"message": error}), 404
    if error == "Insufficient balance":
        return jsonify({"message": error}), 400
    if error:
        return jsonify({"message": error}), 500

    return jsonify({"message": "Payment processed successfully"}), 200


@orders_bp.route('/orders/history', methods=['GET'])
def order_history():
    """API lấy lịch sử đơn hàng của người dùng"""
    from flask import g
    
    # Tự động lấy lịch sử của user đang đăng nhập
    user_id = g.current_user.user_id
    result = services.get_order_history(user_id)

    if len(result) == 0:
        return jsonify({"message": "User has no orders"}), 404

    return jsonify({"orders": result}), 200
