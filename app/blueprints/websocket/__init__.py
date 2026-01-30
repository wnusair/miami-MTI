"""
WebSocket blueprint for real-time communication.
"""
from flask import Blueprint

websocket_bp = Blueprint('websocket', __name__)

from . import routes
