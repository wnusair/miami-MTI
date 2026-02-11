"""
Test cases for all application routes.
"""

import pytest
import json
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Role, SensorData, RolePermission, DEFAULT_PERMISSIONS


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        roles = ['Manager', 'Engineer', 'Operator', 'Investor', 'Audit']
        for role_name in roles:
            role = Role(name=role_name)
            db.session.add(role)
        db.session.commit()
        
        for role_name, perms in DEFAULT_PERMISSIONS.items():
            role = Role.query.filter_by(name=role_name).first()
            if role:
                permission = RolePermission(
                    role_id=role.id,
                    can_view_panel_1=perms['can_view_panel_1'],
                    can_view_panel_2=perms['can_view_panel_2'],
                    can_view_panel_3=perms['can_view_panel_3'],
                    can_view_panel_4=perms['can_view_panel_4'],
                    can_export_data=perms['can_export_data'],
                    can_edit_data=perms['can_edit_data'],
                    can_manage_users=perms['can_manage_users'],
                    can_view_access_logs=perms['can_view_access_logs'],
                )
                db.session.add(permission)
        db.session.commit()
        
        yield app
        
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def create_user_with_role(role_name, username='testuser', password='testpass'):
    """Helper to create a user with a specific role."""
    role = Role.query.filter_by(name=role_name).first()
    user = User(username=username, role_id=role.id)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def login_as(client, username, password='testpass'):
    """Helper to log in as a user."""
    return client.post('/auth/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)


class TestAdminRoutes:
    """Test cases for admin routes."""
    
    def test_admin_users_page_requires_login(self, client):
        """Test admin page requires login."""
        response = client.get('/admin/users', follow_redirects=False)
        assert response.status_code == 302
    
    def test_admin_users_page_requires_manager(self, app, client):
        """Test admin page requires Manager role."""
        with app.app_context():
            create_user_with_role('Investor', 'investor')
        
        login_as(client, 'investor')
        response = client.get('/admin/users', follow_redirects=True)
        assert b'Access denied' in response.data
    
    def test_admin_users_page_loads_for_manager(self, app, client):
        """Test admin page loads for Manager."""
        with app.app_context():
            create_user_with_role('Manager', 'manager')
        
        login_as(client, 'manager')
        response = client.get('/admin/users')
        assert response.status_code == 200
    
    def test_create_user(self, app, client):
        """Test user creation."""
        with app.app_context():
            create_user_with_role('Manager', 'manager')
            engineer_role = Role.query.filter_by(name='Engineer').first()
        
        login_as(client, 'manager')
        response = client.post('/admin/users/create', data={
            'username': 'newuser',
            'password': 'newpass',
            'role_id': engineer_role.id
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'created successfully' in response.data
        
        with app.app_context():
            user = User.query.filter_by(username='newuser').first()
            assert user is not None
            assert user.has_role('Engineer')
    
    def test_create_user_duplicate_username(self, app, client):
        """Test creating user with duplicate username fails."""
        with app.app_context():
            create_user_with_role('Manager', 'manager')
            create_user_with_role('Engineer', 'existing')
            engineer_role = Role.query.filter_by(name='Engineer').first()
        
        login_as(client, 'manager')
        response = client.post('/admin/users/create', data={
            'username': 'existing',
            'password': 'pass',
            'role_id': engineer_role.id
        }, follow_redirects=True)
        
        assert b'already exists' in response.data
    
    def test_create_user_missing_fields(self, app, client):
        """Test creating user with missing fields fails."""
        with app.app_context():
            create_user_with_role('Manager', 'manager')
        
        login_as(client, 'manager')
        response = client.post('/admin/users/create', data={
            'username': 'incomplete'
        }, follow_redirects=True)
        
        assert b'required' in response.data.lower()
    
    def test_delete_user(self, app, client):
        """Test user deletion."""
        with app.app_context():
            create_user_with_role('Manager', 'manager')
            target_user = create_user_with_role('Engineer', 'target')
            target_id = target_user.id
        
        login_as(client, 'manager')
        response = client.post(f'/admin/users/{target_id}/delete', follow_redirects=True)
        
        assert b'deleted successfully' in response.data
        
        with app.app_context():
            user = User.query.filter_by(username='target').first()
            assert user is None
    
    def test_cannot_delete_self(self, app, client):
        """Test user cannot delete themselves."""
        with app.app_context():
            manager = create_user_with_role('Manager', 'manager')
            manager_id = manager.id
        
        login_as(client, 'manager')
        response = client.post(f'/admin/users/{manager_id}/delete', follow_redirects=True)
        
        assert b'cannot delete yourself' in response.data.lower()
        
        with app.app_context():
            user = User.query.filter_by(username='manager').first()
            assert user is not None
    
    def test_reset_password(self, app, client):
        """Test password reset."""
        with app.app_context():
            create_user_with_role('Manager', 'manager')
            target_user = create_user_with_role('Engineer', 'target')
            target_id = target_user.id
        
        login_as(client, 'manager')
        response = client.post(f'/admin/users/{target_id}/reset-password', data={
            'new_password': 'newpassword'
        }, follow_redirects=True)
        
        assert b'reset successfully' in response.data.lower()
        
        with app.app_context():
            user = User.query.filter_by(username='target').first()
            assert user.check_password('newpassword')
    
    def test_permissions_page_loads(self, app, client):
        """Test permissions page loads for Manager."""
        with app.app_context():
            create_user_with_role('Manager', 'manager')
        
        login_as(client, 'manager')
        response = client.get('/admin/permissions')
        assert response.status_code == 200
    
    def test_update_permissions(self, app, client):
        """Test updating role permissions."""
        with app.app_context():
            create_user_with_role('Manager', 'manager')
            investor_role = Role.query.filter_by(name='Investor').first()
        
        login_as(client, 'manager')
        response = client.post(f'/admin/permissions/{investor_role.id}/update', data={
            'can_view_panel_1': 'on',
            'can_view_panel_2': 'on',
            'can_view_panel_3': 'on',
            'can_export_data': 'on'
        }, follow_redirects=True)
        
        assert b'updated successfully' in response.data.lower()
        
        with app.app_context():
            role = Role.query.filter_by(name='Investor').first()
            perms = role.permissions
            assert perms.can_view_panel_3 is True
            assert perms.can_export_data is True


class TestAPIRoutes:
    """Test cases for API routes."""
    
    def test_sensor_data_requires_login(self, client):
        """Test sensor data endpoint requires login."""
        response = client.get('/api/sensor-data', follow_redirects=False)
        assert response.status_code == 302
    
    def test_get_sensor_data(self, app, client):
        """Test getting sensor data."""
        with app.app_context():
            create_user_with_role('Manager', 'manager')
            for i in range(5):
                sensor = SensorData(
                    sensor_name='Test_Sensor',
                    value=float(i),
                    unit='deg',
                    status='OK'
                )
                db.session.add(sensor)
            db.session.commit()
        
        login_as(client, 'manager')
        response = client.get('/api/sensor-data')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) <= 100
    
    def test_get_sensor_data_with_filter(self, app, client):
        """Test getting sensor data with sensor name filter."""
        with app.app_context():
            create_user_with_role('Manager', 'manager')
            sensor1 = SensorData(sensor_name='Sensor_A', value=1.0, unit='deg', status='OK')
            sensor2 = SensorData(sensor_name='Sensor_B', value=2.0, unit='deg', status='OK')
            db.session.add(sensor1)
            db.session.add(sensor2)
            db.session.commit()
        
        login_as(client, 'manager')
        response = client.get('/api/sensor-data?sensor_name=Sensor_A')
        
        data = json.loads(response.data)
        assert all(item['sensor_name'] == 'Sensor_A' for item in data)
    
    def test_get_latest_sensor_data(self, app, client):
        """Test getting latest sensor data."""
        with app.app_context():
            create_user_with_role('Manager', 'manager')
            sensor1 = SensorData(sensor_name='Sensor_A', value=1.0, unit='deg', status='OK')
            sensor2 = SensorData(sensor_name='Sensor_B', value=2.0, unit='deg', status='OK')
            db.session.add(sensor1)
            db.session.add(sensor2)
            db.session.commit()
        
        login_as(client, 'manager')
        response = client.get('/api/sensor-data/latest')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 2
    
    def test_get_sensor_stats(self, app, client):
        """Test getting sensor statistics."""
        with app.app_context():
            create_user_with_role('Manager', 'manager')
            for i in range(10):
                sensor = SensorData(
                    sensor_name=f'Sensor_{i % 3}',
                    value=float(i),
                    unit='deg',
                    status='OK'
                )
                db.session.add(sensor)
            db.session.commit()
        
        login_as(client, 'manager')
        response = client.get('/api/sensor-data/stats')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_readings' in data
        assert 'sensor_count' in data
        assert 'avg_value' in data
        assert data['total_readings'] == 10
    
    def test_export_requires_permission(self, app, client):
        """Test export requires export permission."""
        with app.app_context():
            create_user_with_role('Investor', 'investor')
        
        login_as(client, 'investor')
        response = client.get('/api/export')
        
        assert response.status_code == 403
    
    def test_export_with_permission(self, app, client):
        """Test export works with correct permission."""
        with app.app_context():
            create_user_with_role('Manager', 'manager')
            sensor = SensorData(sensor_name='Test', value=1.0, unit='deg', status='OK')
            db.session.add(sensor)
            db.session.commit()
        
        login_as(client, 'manager')
        response = client.get('/api/export')
        
        assert response.status_code == 200
        assert response.content_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    def test_ingest_sensor_data_single(self, app, client):
        """Test ingesting single sensor data."""
        with app.app_context():
            pass
        
        response = client.post('/api/ingest', 
            data=json.dumps({
                'sensor_name': 'Test_Sensor',
                'value': 42.5,
                'unit': 'deg',
                'status': 'OK'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['created'] == 1
        
        with app.app_context():
            sensor = SensorData.query.first()
            assert sensor is not None
            assert sensor.sensor_name == 'Test_Sensor'
            assert sensor.value == 42.5
    
    def test_ingest_sensor_data_batch(self, app, client):
        """Test ingesting batch sensor data."""
        payload = [
            {'sensor_name': 'Sensor_A', 'value': 1.0, 'unit': 'deg', 'status': 'OK'},
            {'sensor_name': 'Sensor_B', 'value': 2.0, 'unit': 'deg', 'status': 'OK'},
            {'sensor_name': 'Sensor_C', 'value': 3.0, 'unit': 'deg', 'status': 'OK'}
        ]
        
        response = client.post('/api/ingest',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['created'] == 3
    
    def test_ingest_invalid_data(self, app, client):
        """Test ingesting invalid sensor data."""
        response = client.post('/api/ingest',
            data=json.dumps({'invalid': 'data'}),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['created'] == 0


class TestDashboardRoutes:
    """Test cases for dashboard routes."""
    
    def test_dashboard_requires_login(self, client):
        """Test dashboard requires login."""
        response = client.get('/dashboard/', follow_redirects=False)
        assert response.status_code == 302
    
    def test_dashboard_loads_for_authenticated_user(self, app, client):
        """Test dashboard loads for authenticated user."""
        with app.app_context():
            create_user_with_role('Manager', 'manager')
        
        login_as(client, 'manager')
        response = client.get('/dashboard/')
        
        assert response.status_code == 200
    
    def test_dashboard_panel_permissions(self, app, client):
        """Test dashboard respects panel permissions."""
        with app.app_context():
            create_user_with_role('Investor', 'investor')
        
        login_as(client, 'investor')
        response = client.get('/dashboard/')
        
        assert response.status_code == 200


class TestGameRoutes:
    """Test cases for game routes."""
    
    def test_game_embed_requires_login(self, client):
        """Test game embed requires login."""
        response = client.get('/game/embed', follow_redirects=False)
        assert response.status_code == 302
    
    def test_game_frame_requires_login(self, client):
        """Test game frame requires login."""
        response = client.get('/game/frame', follow_redirects=False)
        assert response.status_code == 302
    
    def test_game_frame_loads_for_authenticated_user(self, app, client):
        """Test game frame loads for authenticated user."""
        with app.app_context():
            create_user_with_role('Manager', 'manager')
        
        login_as(client, 'manager')
        response = client.get('/game/frame')
        
        assert response.status_code == 200
        assert b'iframe' in response.data.lower()
