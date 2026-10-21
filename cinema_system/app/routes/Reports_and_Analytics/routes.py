from flask import Blueprint, request, jsonify
from . import services

# Blueprint với tiền tố /api/admin/reports (Middleware tự động kiểm tra token và quyền Admin)
admin_bp = Blueprint('analytics', __name__, url_prefix='/api/admin/reports')


@admin_bp.route('/revenue', methods=['GET'])
def revenue_report():
    """
    [Admin - Báo cáo doanh thu]
    Query Params:
      - start_date (YYYY-MM-DD, optional): Ngày bắt đầu
      - end_date   (YYYY-MM-DD, optional): Ngày kết thúc
      - cinema_id  (int, optional): Lọc theo cụm rạp
      - movie_id   (int, optional): Lọc theo phim
    Header:
      - Authorization: Bearer <token_admin>
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    cinema_id = request.args.get('cinema_id')
    movie_id = request.args.get('movie_id')

    success, result = services.get_revenue_report(
        start_date=start_date,
        end_date=end_date,
        cinema_id=cinema_id,
        movie_id=movie_id
    )

    if not success:
        return jsonify({
            "status": "error",
            "message": result
        }), 400

    return jsonify({
        "status": "success",
        "data": result
    }), 200


@admin_bp.route('/movies', methods=['GET'])
def top_movies_report():
    """
    [Admin - Báo cáo hiệu suất phim & Top phim ăn khách]
    Query Params:
      - start_date (YYYY-MM-DD, optional): Ngày bắt đầu
      - end_date   (YYYY-MM-DD, optional): Ngày kết thúc
      - limit      (int, optional, default=10): Số lượng phim hiển thị
    Header:
      - Authorization: Bearer <token_admin>
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = request.args.get('limit', 10)

    success, result = services.get_top_movies_report(
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )

    if not success:
        return jsonify({
            "status": "error",
            "message": result
        }), 400

    return jsonify({
        "status": "success",
        "total": len(result),
        "data": result
    }), 200


@admin_bp.route('/overview', methods=['GET'])
def overview_report():
    """
    [Admin - Báo cáo tổng quan Dashboard]
    Tổng hợp: Tổng doanh thu, tổng vé bán, số đơn hàng, khách hàng, phim, rạp.
    Header:
      - Authorization: Bearer <token_admin>
    """
    success, result = services.get_overview_report()
    if not success:
        return jsonify({
            "status": "error",
            "message": result
        }), 500

    return jsonify({
        "status": "success",
        "data": result
    }), 200


@admin_bp.route('/cinemas', methods=['GET'])
def cinemas_report():
    """
    [Admin - Báo cáo hiệu suất kinh doanh theo cụm rạp]
    Query Params:
      - start_date (YYYY-MM-DD, optional)
      - end_date   (YYYY-MM-DD, optional)
    Header:
      - Authorization: Bearer <token_admin>
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    success, result = services.get_cinema_performance_report(
        start_date=start_date,
        end_date=end_date
    )

    if not success:
        return jsonify({
            "status": "error",
            "message": result
        }), 400

    return jsonify({
        "status": "success",
        "total": len(result),
        "data": result
    }), 200