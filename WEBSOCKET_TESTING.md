# WebSocket Testing Guide

## Overview

Testing WebSocket requires two components:
1. **MTI Server** - The main application (runs on port 5000)
2. **Test Client** - A separate client app (runs on port 5001) to simulate external device connections

## Development Testing

### 1. Start the MTI Server
```bash
python run.py
```
Server runs at `http://localhost:5000`

### 2. Start the Test Client (on a separate device or terminal)
```bash
cd scripts
python websocket_client_app.py
```
Client runs at `http://localhost:5001`

### 3. Connect
1. Open `http://localhost:5001` in browser
2. Click "Local (Dev)" button to set server URL
3. Click "Connect"

## Production Testing

### 1. Start the Test Client
```bash
cd scripts
python websocket_client_app.py
```

### 2. Connect to Production
1. Open `http://localhost:5001` in browser
2. Click "Production" button
3. Click "Connect"

### CORS Configuration
Production server needs proper CORS origins in `.env`:
```
SOCKETIO_CORS_ORIGINS=https://mti.wnusair.org,https://www.mti.wnusair.org
```

## Test Features

### Latency Test
- **Ping**: Single round-trip measurement
- **Auto**: Continuous 1-second pings
- **Stop**: Stop auto ping
- **Reset**: Clear stored data

Stats stored in localStorage, persist across sessions.

### Stress Test
Sends configurable messages (1-1000) rapidly. Tracks sent/received/lost.

### Data Types
- **Number**: Numeric values
- **Message**: Text strings
- **JSON**: Arbitrary JSON payloads
- **Image**: Compressed images (see below)

### Image Sending
Large images cause disconnection due to SocketIO message limits. Use the compression controls:
- **Quality**: JPEG compression (10-100%)
- **Max Size**: Maximum dimension in pixels (100-1000px)

Recommended settings for reliable transmission:
- Quality: 50%
- Max Size: 400px

## Viewing Test Data

### Latency Stats
- Test client: Stored in `localStorage.latency_stats`
- Main app: Stored in `latency_stats` cookie

Open browser DevTools > Application > Local Storage or Cookies to view raw data.

### Event Log
Both client and server demo pages show real-time event logs.

## Removing Test Features

Test code is marked with `DELETE WHEN DONE TESTING` comments.

To remove:
1. Delete `app/blueprints/websocket/routes.py` section between `DEMO/TEST HANDLERS` markers
2. Delete `app/templates/websocket/demo.html`
3. Delete `scripts/websocket_client_app.py`
4. Remove WebSocket nav link from `app/templates/base.html`

Keep these core handlers:
- `connect`
- `disconnect`
- `join_room`
- `leave_room`
- `panel_update`
- `ping_latency`
