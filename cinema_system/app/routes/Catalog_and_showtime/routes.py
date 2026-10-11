from flask import Blueprint, request, jsonify
from . import services

catalog_bp = Blueprint('catalog', __name__, url_prefix='/api')

@catalog_bp.route('/movies', methods=['GET'])
def list_movies():
    pass

@catalog_bp.route('/cinemas', methods=['GET'])
def list_cinemas():
    pass

@catalog_bp.route('/showtimes', methods=['GET'])
def list_showtimes():
    pass

@catalog_bp.route('/admin/movies', methods=['POST'])
def add_movie():
    pass

@catalog_bp.route('/admin/showtimes', methods=['POST'])
def add_showtime():
    pass