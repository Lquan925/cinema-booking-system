"""Swagger UI cho tài liệu OpenAPI của hệ thống.

- GET /api/docs                → giao diện Swagger UI
- GET /api/docs/specs/<file>   → file YAML trong thư mục "API spec"
"""
from pathlib import Path

from flask import Blueprint, render_template_string, send_from_directory

SPEC_DIR = Path(__file__).resolve().parent.parent / "API spec"

SPEC_FILES = [
    ("user_management.yaml", "1. User Management"),
    ("booking_and_seat.yaml", "2. Booking and Seat"),
    ("orders_and_payments.yaml", "3. Orders and Payments"),
    ("catalog_and_showtime.yaml", "4. Catalog and Showtime"),
    ("reports_and_analytics.yaml", "5. Reports and Analytics"),
]

SWAGGER_UI_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Cinema Booking System - API Docs</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui.css">
  <style>
    html { box-sizing: border-box; overflow-y: scroll; }
    *, *::before, *::after { box-sizing: inherit; }
    body { margin: 0; background: #fafafa; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui-standalone-preset.js"></script>
  <script>
    window.ui = SwaggerUIBundle({
      urls: {{ spec_urls | tojson }},
      "urls.primaryName": "1. User Management",
      dom_id: '#swagger-ui',
      deepLinking: true,
      displayRequestDuration: true,
      persistAuthorization: true,
      filter: true,
      presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
      layout: 'StandaloneLayout'
    });
  </script>
</body>
</html>
"""

docs_bp = Blueprint('docs', __name__)


@docs_bp.route('/api/docs')
@docs_bp.route('/api/docs/')
def swagger_ui():
    spec_urls = [
        {"url": f"/api/docs/specs/{filename}", "name": name}
        for filename, name in SPEC_FILES
    ]
    return render_template_string(SWAGGER_UI_HTML, spec_urls=spec_urls)


@docs_bp.route('/api/docs/specs/<path:filename>')
def serve_spec(filename):
    return send_from_directory(SPEC_DIR, filename, mimetype='application/yaml')
