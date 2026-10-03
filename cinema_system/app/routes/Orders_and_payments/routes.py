from flask import Blueprint, request, jsonify
from . import services
from app import db
from app.models import Order, Ticket, User
import uuid

orders_bp = Blueprint('orders_and_payments', __name__, url_prefix='/api')

@orders_bp.route('/orders/<int:user_id>', methods=['POST'])
def create_order(user_id):
    data = request.get_json(silent=True) or {}
    ticket_ids = data.get("ticket_ids", [])
    
    if not ticket_ids:
        return jsonify({"message": "Vui lòng chọn ít nhất 1 vé!"}), 400
    
    tickets = Ticket.query.filter(Ticket.ticket_id.in_(ticket_ids)).all()
    total_amount = services.get_total_amount(tickets)
    
    new_order = Order(
        user_id = user_id,
        total_amount = total_amount,
        status = "pending"
    )
    
    db.session.add(new_order)
    db.session.flush()
    
    for ticket in tickets:
        ticket.order_id = new_order.order_id
        ticket.status = "pending"
    
    db.session.commit()
    
    return jsonify({"message": "Order created successfully", "order_id": new_order.order_id}), 201


@orders_bp.route('/payments/process/<string:order_id>', methods=['POST'])
def process_payment(order_id):
    order = Order.query.filter(Order.order_id == order_id).first()
    if not order:
        return jsonify({"message": "Order not found"}), 404
    user_id = order.user_id
    user = User.query.filter(User.user_id == user_id).first()
    if not user:
        return jsonify({"message": "User not found"}), 404
        
    if user.wallet_balance < order.total_amount:
        return jsonify({"message": "Insufficient balance"}), 400
        
    user.loyalty_points += 1
    user.wallet_balance -= order.total_amount

    order.status = "success"
    
    tickets = Ticket.query.filter(Ticket.order_id == order_id).all()
    for ticket in tickets:
        ticket.status = "ready"
        ticket.qr_code_url = f"https://example.com/qr/{uuid.uuid4()}"
    db.session.commit()
    return jsonify({"message": "Payment processed successfully"}), 200
    

@orders_bp.route('/orders/<int:user_id>/history', methods=['GET'])
def order_history(user_id):
    orders = Order.query.filter(Order.user_id == user_id).all()
    result = []
    for order in orders:
        result.append({
            "user_id": order.user_id,
            "order_id": order.order_id,
            "total_amount": float(order.total_amount),
            "status": order.status
        })
    if len(result) == 0:
        return jsonify({"message": "User has no orders"}), 404
    return jsonify({"orders": result}), 200