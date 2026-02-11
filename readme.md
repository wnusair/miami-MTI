# Miami Telemetry Interface

## File Structure

```
app/
  blueprints/        
    admin/           
    api/             
    auth/            
    dashboard/       
    game/            
    websocket/       
  models/            # SQLAlchemy models
    user_models.py   # User, Role
    sensor_models.py # SensorData
    permission_models.py # RolePermission, DEFAULT_PERMISSIONS
  static/
    css/             
    js/              # dashboard.js (Chart.js rendering, WebSocket client)
  templates/         
scripts/             
tests/               
config.py            
run.py              
```

## Nomenclature

- Models use PascalCase: `SensorData`, `RolePermission`
- Routes use snake_case: `grid_view()`, `get_sensor_data()`
- Database tables use snake_case: `sensor_data`, `role_permissions`
- Blueprints registered with `_bp` suffix: `admin_bp`, `api_bp`
- Templates organized by blueprint in `templates/{blueprint}/`

## Comment Style

Docstrings on all modules, classes, and public functions. Inline comments only for non-obvious logic. Routes have single-line docstrings describing purpose. Models include field-level comments for permissions.

## Code Organization

Application factory pattern in `app/__init__.py`. Extensions initialized in `extensions.py` to avoid circular imports. Blueprints keep routes, logic separate. Decorators like `@login_required` and `@manager_required` enforce access control. Config loaded from environment via `python-dotenv`.

## Setup

### Environment Variables

Create `.env` file:

```
SECRET_KEY=your-secret-key-here
FLASK_CONFIG=development
DATABASE_URL=sqlite:///db.sqlite3
SOCKETIO_CORS_ORIGINS=*
```

Generate secret key: `python -c "import secrets; print(secrets.token_hex(32))"`

### Install Dependencies

```powershell
pip install -r requirements.txt
```

### Initialize Database

```powershell
python scripts/seed_database.py
```

Creates 5 roles (Manager, Engineer, Operator, Investor, Audit), sets default permissions, generates admin user with random password.

### Run Development Server

```powershell
python run.py
```

Runs on `http://localhost:5000` with WebSocket support.

### Run Mock Data Generator

Simulates sensor telemetry in separate terminal:

```powershell
python scripts/mock_data_stream.py
```

Generates 6 sensor readings per second (Arm_Servo_1, Arm_Servo_2, Motor_Temp, Motor_RPM, Battery_Voltage, System_Load).

## Role Permissions

5 roles with hierarchical permissions:

- Investor: Panels 1-2 only (live feed, KPIs)
- Audit: Panels 1-3, export data, view access logs
- Operator: All 4 panels, no export
- Engineer: All panels, export, edit data
- Manager: Full access, admin panel, user management

Configurable per-role via admin interface at `/admin/permissions`.

## Features

### Authentication

Login at `/auth/login`. Logout at `/auth/logout`. Passwords hashed with `werkzeug.security`. Session management via Flask-Login.

### Dashboard

4-panel grid at `/dashboard/`:

1. Live sensor feed with Chart.js line charts
2. Current status KPIs (readings count, sensor count, avg value, status summary)
3. Historical logs (time-range filtering)
4. Device health (VR game embed + camera feed)

Each panel has fullscreen toggle. Data auto-refreshes every 50ms. WebSocket updates for real-time streaming.

### Admin Panel

Manager-only routes at `/admin/`:

- `/admin/users` - create, delete, reset passwords
- `/admin/permissions` - configure role permissions via checkboxes

### API Endpoints

REST API at `/api/`:

- `GET /api/sensor-data` - query sensor data with filters (sensor_name, hours, limit)
- `GET /api/sensor-data/latest` - latest reading per sensor
- `GET /api/sensor-data/stats` - aggregate stats for KPIs
- `GET /api/export` - download XLSX with date range filters (permission-gated)
- `POST /api/ingest` - insert sensor data from external sources (no auth)

### WebSocket Events

Real-time bidirectional communication:

Server handlers:
- `connect` - client connection, track connected clients
- `disconnect` - cleanup on disconnect
- `join_room` - join room for targeted broadcasts
- `panel_update` - emit data updates to dashboard room
- `ping_latency` - latency measurement

Test handlers (marked DELETE WHEN DONE TESTING):
- `broadcast_message`, `send_number`, `send_json`, `send_image`
- `stress_test` - performance testing

Demo page at `/ws/demo` for testing WebSocket connectivity.

### Game Integration

itch.io embed proxy at `/game/frame`. Fetches game HTML server-side, rewrites URLs to bypass X-Frame-Options restrictions. Login required.

### Data Export

Excel export with openpyxl formatting. Columns auto-sized. Filename includes timestamp. Respects user export permission.

## CLI Commands

Flask CLI via `run.py`:

```powershell
# Seed roles
flask seed_roles

# Create admin user
flask seed_admin

# Interactive shell with models loaded
flask shell
```

## Scripts

### seed_database.py

Full database initialization with roles, permissions, users. Generates secure random passwords.

### mock_data_stream.py

Simulates sensor data stream. Runs continuously until Ctrl+C. Inserts readings every 1 second.

### reset_passwords.py

Password management utility:

```powershell
# Reset single user
python scripts/reset_passwords.py --user alice --password NewPass123!

# Reset all users to random passwords
python scripts/reset_passwords.py --all --random --length 16
```

### websocket_client_app.py

Standalone WebSocket test client. Flask app on port 5001. Tests latency, stress testing, message broadcasting. DELETE WHEN DONE TESTING.

## Testing

pytest configuration in `pytest.ini`. Tests use in-memory SQLite database.

### Run All Tests

```powershell
pytest
```

### Run Specific Test File

```powershell
pytest tests/test_routes.py
pytest tests/test_permissions.py
```

### Run with Coverage

```powershell
pytest --cov=app --cov-report=html
```

Test files:
- `test_routes.py` - all HTTP endpoints (446 lines, covers auth, admin, API, dashboard)
- `test_permissions.py` - role-based access control (276 lines, tests all 5 roles)
- `test_config.py` - environment configuration
- `test_edge_cases.py` - error handling, edge conditions
- `test_app.py` - app factory, extensions

## Deployment

### Production Config

Set environment:

```
FLASK_CONFIG=production
SOCKETIO_CORS_ORIGINS=https://mti.wnusair.org,https://www.mti.wnusair.org
```

### Run with Gunicorn

```powershell
gunicorn -k eventlet -w 1 -b 0.0.0.0:5000 run:app
```

Single worker with eventlet required for WebSocket support.

## What This App Does

Receives sensor telemetry data via POST to `/api/ingest`, stores in SQLite, displays on real-time dashboard with role-based access, exports to Excel, streams updates via WebSocket, embeds VR visualization, enforces granular permissions per role, manages users via admin interface.

## Configuration Notes

- SECRET_KEY validated at startup (min 16 chars)
- CORS origins configurable per environment
- Database URI defaults to SQLite, supports PostgreSQL
- Debug mode disabled in production config
- WebSocket async mode set to threading
- Blueprints have url_prefix to namespace routes

## Removing Test Code

Delete these when testing complete:

1. `/app/blueprints/websocket/routes.py` lines marked DELETE WHEN DONE TESTING
2. `/app/templates/websocket/demo.html`
3. `/scripts/websocket_client_app.py`
4. WebSocket nav link in `/app/templates/base.html`

Keep core WebSocket handlers: connect, disconnect, join_room, leave_room, panel_update, ping_latency.

## Database Schema

3 core tables:

- `users` - id, username, password_hash, role_id
- `roles` - id, name
- `role_permissions` - id, role_id, 8 boolean permission fields
- `sensor_data` - id, timestamp, sensor_name, value, unit, status

Foreign keys: User.role_id -> Role.id, RolePermission.role_id -> Role.id

## Frontend

Chart.js for live/historical charts. Socket.IO client for WebSocket. Vanilla JS, no framework. Miami University brand colors (red #C3142D, black #000000, gray #757575). Responsive grid layout. Fullscreen panel mode with ESC key exit.

## Security

- Password hashing via werkzeug
- SECRET_KEY validation at startup
- Role-based route decorators
- CSRF protection (can be disabled for testing)
- Login required on all dashboard/admin routes
- API ingestion endpoint has no auth (intended for IoT devices)

## Error Handling

404/403 errors return flash messages. Validation errors on user creation. Permission checks return 403 with descriptive message. Database commit failures rolled back.

## Monitoring

Connected client count tracked in memory. WebSocket latency measurement via ping/pong. Stress test handler for load testing. Sensor status field (OK/WARNING/ERROR) based on value thresholds.
