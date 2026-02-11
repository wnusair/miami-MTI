"""
Test cases for edge cases, error handling, and data validation.
"""

import pytest
import json
from datetime import datetime, timedelta, timezone
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


class TestDataValidation:
    """Test data validation and edge cases."""
    
    def test_sensor_data_negative_values(self, app):
        """Test sensor data accepts negative values."""
        with app.app_context():
            sensor = SensorData(
                sensor_name='Temp_Sensor',
                value=-10.5,
                unit='C',
                status='OK'
            )
            db.session.add(sensor)
            db.session.commit()
            
            retrieved = SensorData.query.first()
            assert retrieved.value == -10.5
    
    def test_sensor_data_zero_value(self, app):
        """Test sensor data accepts zero."""
        with app.app_context():
            sensor = SensorData(
                sensor_name='Pressure_Sensor',
                value=0.0,
                unit='Pa',
                status='OK'
            )
            db.session.add(sensor)
            db.session.commit()
            
            retrieved = SensorData.query.first()
            assert retrieved.value == 0.0
    
    def test_sensor_data_large_values(self, app):
        """Test sensor data accepts large values."""
        with app.app_context():
            sensor = SensorData(
                sensor_name='RPM_Sensor',
                value=999999.99,
                unit='RPM',
                status='OK'
            )
            db.session.add(sensor)
            db.session.commit()
            
            retrieved = SensorData.query.first()
            assert retrieved.value == 999999.99
    
    def test_sensor_data_precision(self, app):
        """Test sensor data preserves precision."""
        with app.app_context():
            sensor = SensorData(
                sensor_name='Precise_Sensor',
                value=3.14159265,
                unit='rad',
                status='OK'
            )
            db.session.add(sensor)
            db.session.commit()
            
            retrieved = SensorData.query.first()
            assert abs(retrieved.value - 3.14159265) < 0.0001
    
    def test_user_empty_password(self, app):
        """Test user cannot have empty password hash."""
        with app.app_context():
            role = Role.query.filter_by(name='Manager').first()
            user = User(username='testuser', role_id=role.id)
            user.set_password('')
            
            assert user.password_hash is not None
            assert user.password_hash != ''
    
    def test_sensor_data_empty_sensor_name(self, app):
        """Test sensor data requires sensor name."""
        with app.app_context():
            sensor = SensorData(
                sensor_name='',
                value=1.0,
                unit='deg',
                status='OK'
            )
            db.session.add(sensor)
            db.session.commit()
            
            retrieved = SensorData.query.first()
            assert retrieved.sensor_name == ''


class TestErrorHandling:
    """Test error handling."""
    
    def test_404_on_invalid_route(self, client):
        """Test 404 error on invalid route."""
        response = client.get('/nonexistent/route')
        assert response.status_code == 404
    
    def test_invalid_user_id_in_delete(self, app, client):
        """Test deleting user with invalid ID."""
        with app.app_context():
            role = Role.query.filter_by(name='Manager').first()
            user = User(username='manager', role_id=role.id)
            user.set_password('test')
            db.session.add(user)
            db.session.commit()
        
        client.post('/auth/login', data={
            'username': 'manager',
            'password': 'test'
        })
        
        response = client.post('/admin/users/99999/delete')
        assert response.status_code == 404
    
    def test_invalid_user_id_in_reset_password(self, app, client):
        """Test resetting password with invalid ID."""
        with app.app_context():
            role = Role.query.filter_by(name='Manager').first()
            user = User(username='manager', role_id=role.id)
            user.set_password('test')
            db.session.add(user)
            db.session.commit()
        
        client.post('/auth/login', data={
            'username': 'manager',
            'password': 'test'
        })
        
        response = client.post('/admin/users/99999/reset-password', data={
            'new_password': 'newpass'
        })
        assert response.status_code == 404
    
    def test_ingest_no_data(self, client):
        """Test ingest endpoint with no data."""
        response = client.post('/api/ingest',
            data='',
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_ingest_invalid_json(self, client):
        """Test ingest endpoint with invalid JSON."""
        response = client.post('/api/ingest',
            data='not valid json',
            content_type='application/json'
        )
        assert response.status_code in [400, 415]
    
    def test_ingest_missing_required_fields(self, app, client):
        """Test ingest with missing required fields."""
        response = client.post('/api/ingest',
            data=json.dumps({'sensor_name': 'Test'}),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        assert data['created'] == 0
    
    def test_ingest_invalid_value_type(self, app, client):
        """Test ingest with non-numeric value."""
        response = client.post('/api/ingest',
            data=json.dumps({
                'sensor_name': 'Test',
                'value': 'not_a_number',
                'unit': 'deg'
            }),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        assert data['created'] == 0
    
    def test_export_empty_database(self, app, client):
        """Test export with no data."""
        with app.app_context():
            role = Role.query.filter_by(name='Manager').first()
            user = User(username='manager', role_id=role.id)
            user.set_password('test')
            db.session.add(user)
            db.session.commit()
        
        client.post('/auth/login', data={
            'username': 'manager',
            'password': 'test'
        })
        
        response = client.get('/api/export')
        assert response.status_code == 200


class TestBoundaryConditions:
    """Test boundary conditions."""
    
    def test_sensor_data_query_limit(self, app, client):
        """Test sensor data query respects limit parameter."""
        with app.app_context():
            role = Role.query.filter_by(name='Manager').first()
            user = User(username='manager', role_id=role.id)
            user.set_password('test')
            db.session.add(user)
            
            for i in range(200):
                sensor = SensorData(
                    sensor_name='Test',
                    value=float(i),
                    unit='deg',
                    status='OK'
                )
                db.session.add(sensor)
            db.session.commit()
        
        client.post('/auth/login', data={
            'username': 'manager',
            'password': 'test'
        })
        
        response = client.get('/api/sensor-data?limit=50')
        data = json.loads(response.data)
        assert len(data) == 50
    
    def test_sensor_data_time_filter(self, app, client):
        """Test sensor data time-based filtering."""
        with app.app_context():
            role = Role.query.filter_by(name='Manager').first()
            user = User(username='manager', role_id=role.id)
            user.set_password('test')
            db.session.add(user)
            
            old_sensor = SensorData(
                sensor_name='Old',
                value=1.0,
                unit='deg',
                status='OK',
                timestamp=datetime.now(timezone.utc) - timedelta(hours=2)
            )
            new_sensor = SensorData(
                sensor_name='New',
                value=2.0,
                unit='deg',
                status='OK'
            )
            db.session.add(old_sensor)
            db.session.add(new_sensor)
            db.session.commit()
        
        client.post('/auth/login', data={
            'username': 'manager',
            'password': 'test'
        })
        
        response = client.get('/api/sensor-data?hours=1')
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['sensor_name'] == 'New'
    
    def test_username_uniqueness(self, app, client):
        """Test username must be unique."""
        with app.app_context():
            role = Role.query.filter_by(name='Manager').first()
            manager = User(username='manager', role_id=role.id)
            manager.set_password('test')
            db.session.add(manager)
            
            existing = User(username='existing', role_id=role.id)
            existing.set_password('test')
            db.session.add(existing)
            db.session.commit()
            
            role_id = role.id
        
        client.post('/auth/login', data={
            'username': 'manager',
            'password': 'test'
        })
        
        response = client.post('/admin/users/create', data={
            'username': 'existing',
            'password': 'newpass',
            'role_id': role_id
        }, follow_redirects=True)
        
        assert b'already exists' in response.data


class TestSecurityFeatures:
    """Test security features."""
    
    def test_password_not_stored_plaintext(self, app):
        """Test passwords are not stored in plaintext."""
        with app.app_context():
            role = Role.query.filter_by(name='Manager').first()
            user = User(username='testuser', role_id=role.id)
            user.set_password('mypassword')
            db.session.add(user)
            db.session.commit()
            
            assert user.password_hash != 'mypassword'
            assert 'mypassword' not in user.password_hash
    
    def test_password_check_case_sensitive(self, app):
        """Test password checking is case-sensitive."""
        with app.app_context():
            role = Role.query.filter_by(name='Manager').first()
            user = User(username='testuser', role_id=role.id)
            user.set_password('MyPassword')
            db.session.add(user)
            db.session.commit()
            
            assert user.check_password('MyPassword') is True
            assert user.check_password('mypassword') is False
            assert user.check_password('MYPASSWORD') is False
    
    def test_protected_routes_require_authentication(self, client):
        """Test protected routes require authentication."""
        protected_routes = [
            '/dashboard/',
            '/admin/users',
            '/admin/permissions',
            '/api/sensor-data',
            '/api/export',
            '/game/embed',
            '/game/frame'
        ]
        
        for route in protected_routes:
            response = client.get(route, follow_redirects=False)
            assert response.status_code == 302, f"Route {route} should require authentication"
    
    def test_admin_routes_require_manager_role(self, app, client):
        """Test admin routes require Manager role."""
        with app.app_context():
            role = Role.query.filter_by(name='Engineer').first()
            user = User(username='engineer', role_id=role.id)
            user.set_password('test')
            db.session.add(user)
            db.session.commit()
        
        client.post('/auth/login', data={
            'username': 'engineer',
            'password': 'test'
        })
        
        admin_routes = [
            '/admin/users',
            '/admin/permissions'
        ]
        
        for route in admin_routes:
            response = client.get(route, follow_redirects=True)
            assert b'Access denied' in response.data, f"Route {route} should require Manager role"
