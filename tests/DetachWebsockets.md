# WebSocket Guide


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


### CORS Configuration
Production server needs proper CORS origins in `.env`:
```
SOCKETIO_CORS_ORIGINS=https://mti.wnusair.org,https://www.mti.wnusair.org
```


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
