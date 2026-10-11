from flask import Blueprint, request, jsonify
from . import services

catalog_bp = Blueprint('catalog', __name__, url_prefix='/api')

@catalog_bp.route('/movies', methods=['GET'])
def list_movies():
    movies = services.list_movies()
    return jsonify({"data": movies}), 200

@catalog_bp.route('/cinemas', methods=['GET'])
def list_cinemas():
    cinemas = services.list_cinemas()
    return jsonify({"data": cinemas}), 200

@catalog_bp.route('/showtimes', methods=['GET'])
def list_showtimes():
    try:
        showtimes = services.list_showtimes(
            date=request.args.get("date"),
            movie_id=request.args.get("movie_id"),
            cinema_id=request.args.get("cinema_id"),
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({"data": showtimes}), 200

@catalog_bp.route('/admin/movies', methods=['POST'])
def add_movie():
    if not request.is_json:
        return jsonify({
            "error": "Cần gửi application/json"
        }), 415

    movie_data = request.get_json(silent=True)

    if not isinstance(movie_data, dict):
        return jsonify({
            "error": "Body phải là JSON object hợp lệ"
        }), 400

    try:
        movie_id = services.add_movie(movie_data)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({
        "message": "Movie added successfully",
        "movie_id": movie_id,
    }), 201
    
@catalog_bp.route('/admin/showtimes', methods=['POST'])
def add_showtime():
    if not request.is_json:
        return jsonify({
            "error": "Cần gửi application/json"
        }), 415

    showtime_data = request.get_json(silent=True)

    if not isinstance(showtime_data, dict):
        return jsonify({
            "error": "Body phải là JSON object hợp lệ"
        }), 400

    try:
        showtime_id = services.add_showtime(showtime_data)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    return jsonify({
        "message": "Showtime added successfully",
        "showtime_id": showtime_id,
    }), 201

@catalog_bp.route('/admin/showtimes/<int:showtime_id>', methods=['DELETE'])
def delete_showtime(showtime_id):
    try:
        services.delete_showtime(showtime_id)
    except LookupError as error:
        return jsonify({"error": str(error)}), 404
    except ValueError as error:
        return jsonify({"error": str(error)}), 409

    return "", 204