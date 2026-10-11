from flask import Blueprint, request, jsonify
from . import services

admin_bp = Blueprint('analytics', __name__, url_prefix='/api/admin/reports')

@admin_bp.route('/revenue', methods=['GET'])
def revenue_report():
    pass

@admin_bp.route('/movies', methods=['GET'])
def top_movies_report():
    pass