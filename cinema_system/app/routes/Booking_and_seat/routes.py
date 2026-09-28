from flask import Blueprint, request, jsonify
from . import services

# Gắn tiền tố /api cho toàn bộ các route trong module này
booking_bp = Blueprint('booking', __name__, url_prefix='/api')

@booking_bp.route('/showtimes/<int:showtime_id>/seats', methods=['GET'])
def get_showtime_seats(showtime_id):
    pass

@booking_bp.route('/booking/lock-seat', methods=['POST'])
def api_lock_seat():
    pass

@booking_bp.route('/booking/unlock-seat', methods=['POST'])
def api_unlock_seat():
    pass