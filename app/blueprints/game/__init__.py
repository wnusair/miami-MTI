"""
Game blueprint for MTI.
Handles itch.io game embedding via server-side proxy.
"""
from flask import Blueprint

game_bp = Blueprint('game', __name__)

from . import routes
