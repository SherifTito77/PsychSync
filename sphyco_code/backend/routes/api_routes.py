# backend/routes/api_routes.py
from flask import Blueprint, request, jsonify

# Create a Blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Example route: health check
@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

# Example route: get users (placeholder)
@api_bp.route('/users', methods=['GET'])
def get_users():
    # Replace with real database query later
    users = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"}
    ]
    return jsonify(users), 200
