"""
WebSocket routes and event handlers for real-time communication.

STRUCTURE:
- Core handlers (connect, disconnect, rooms) - Keep these
- Demo/test handlers - Remove when done testing (marked with DELETE WHEN DONE TESTING)
"""
import time
from datetime import datetime
from flask import render_template, Response, request
from flask_login import login_required, current_user
from flask_socketio import emit, join_room, leave_room
from . import websocket_bp
from ...extensions import socketio


connected_clients = {}


# =============================================================================
# CORE WEBSOCKET HANDLERS - Keep these for production
# =============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    client_id = request.sid
    connected_clients[client_id] = {
        'sid': client_id,
        'username': getattr(current_user, 'username', 'anonymous'),
        'connected_at': time.time()
    }
    emit('connection_response', {
        'status': 'connected',
        'client_id': client_id,
        'message': 'Connected to MTI WebSocket server',
        'server_time': time.time() * 1000
    })
    emit('client_count', {'count': len(connected_clients)}, broadcast=True)


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    client_id = request.sid
    if client_id in connected_clients:
        del connected_clients[client_id]
    emit('client_count', {'count': len(connected_clients)}, broadcast=True)


@socketio.on('join_room')
def handle_join_room(data):
    """Handle client joining a room for targeted updates."""
    room = data.get('room', 'default')
    join_room(room)
    emit('room_joined', {'room': room})


@socketio.on('leave_room')
def handle_leave_room(data):
    """Handle client leaving a room."""
    room = data.get('room', 'default')
    leave_room(room)
    emit('room_left', {'room': room})


@socketio.on('panel_update')
def handle_panel_update(data):
    """Handle real-time panel data updates."""
    panel_id = data.get('panel_id')
    panel_data = data.get('data', {})
    
    emit('panel_data', {
        'panel_id': panel_id,
        'data': panel_data,
        'timestamp': datetime.now().isoformat()
    }, room='dashboard')


@socketio.on('ping_latency')
def handle_ping_latency(data):
    """Respond to latency ping with server timestamp."""
    emit('pong_latency', {
        'client_time': data.get('client_time'),
        'server_time': time.time() * 1000
    })


# =============================================================================
# DEMO/TEST HANDLERS - Delete this section when done testing
# =============================================================================

@websocket_bp.route('/demo')
@login_required
def demo():
    """Render the WebSocket demo page. DELETE WHEN DONE TESTING."""
    return render_template('websocket/demo.html')


@socketio.on('join_dashboard')
def handle_join_dashboard(data):
    """Handle client joining dashboard room. DELETE WHEN DONE TESTING."""
    room = data.get('room', 'dashboard')
    join_room(room)
    emit('room_joined', {'room': room, 'message': f'Joined room: {room}'})


@socketio.on('leave_dashboard')
def handle_leave_dashboard(data):
    """Handle client leaving dashboard room. DELETE WHEN DONE TESTING."""
    room = data.get('room', 'dashboard')
    leave_room(room)
    emit('room_left', {'room': room, 'message': f'Left room: {room}'})


@socketio.on('broadcast_message')
def handle_broadcast_message(data):
    """Broadcast a message to all clients. DELETE WHEN DONE TESTING."""
    message = data.get('message', '')
    sender = getattr(current_user, 'username', 'anonymous')
    
    emit('message_received', {
        'sender': sender,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }, broadcast=True)


@socketio.on('send_number')
def handle_send_number(data):
    """Send a number to all clients. DELETE WHEN DONE TESTING."""
    value = data.get('value', 0)
    sender = getattr(current_user, 'username', 'anonymous')
    
    emit('number_received', {
        'sender': sender,
        'value': value,
        'timestamp': datetime.now().isoformat()
    }, broadcast=True)


@socketio.on('send_json')
def handle_send_json(data):
    """Send JSON data to all clients. DELETE WHEN DONE TESTING."""
    payload = data.get('payload', {})
    sender = getattr(current_user, 'username', 'anonymous')
    
    emit('json_received', {
        'sender': sender,
        'payload': payload,
        'timestamp': datetime.now().isoformat()
    }, broadcast=True)


@socketio.on('send_image')
def handle_send_image(data):
    """Send base64 image to all clients. DELETE WHEN DONE TESTING."""
    image_data = data.get('image', '')
    filename = data.get('filename', 'image')
    sender = getattr(current_user, 'username', 'anonymous')
    
    emit('image_received', {
        'sender': sender,
        'image': image_data,
        'filename': filename,
        'timestamp': datetime.now().isoformat()
    }, broadcast=True)


@socketio.on('stress_test')
def handle_stress_test(data):
    """Handle stress test ping. DELETE WHEN DONE TESTING."""
    emit('stress_test_response', {
        'sequence': data.get('sequence', 0),
        'server_time': time.time() * 1000
    })


# =============================================================================
# VIDEO FEED - Keep if using server-side camera streaming
# =============================================================================

@websocket_bp.route('/video_feed')
@login_required
def video_feed():
    """Stream video from a server-connected camera."""
    camera_index = request.args.get('camera', 0, type=int)
    return Response(
        generate_frames(camera_index),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


def generate_frames(camera_index=0):
    """Generator function for camera frames."""
    import cv2
    
    camera = cv2.VideoCapture(camera_index)
    if not camera.isOpened():
        camera = cv2.VideoCapture(0)
    
    try:
        while True:
            success, frame = camera.read()
            if not success:
                break
            
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
                
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    finally:
        camera.release()
