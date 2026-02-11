"""
Unit tests for MTI (Miami Telemetry Interface)

Run tests with: pytest tests/ -v
"""

import pytest
import json
from io import BytesIO
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


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def manager_user(app):
    """Create a manager user."""
    with app.app_context():
        manager_role = Role.query.filter_by(name='Manager').first()
        user = User(username='manager', role_id=manager_role.id)
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def engineer_user(app):
    """Create an engineer user."""
    with app.app_context():
        engineer_role = Role.query.filter_by(name='Engineer').first()
        user = User(username='engineer', role_id=engineer_role.id)
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def investor_user(app):
    """Create an investor user."""
    with app.app_context():
        investor_role = Role.query.filter_by(name='Investor').first()
        user = User(username='investor', role_id=investor_role.id)
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        return user




class TestModels:
    """Test cases for database models."""
    
    def test_role_creation(self, app):
        """Test role creation."""
        with app.app_context():
            role = Role.query.filter_by(name='Manager').first()
            assert role is not None
            assert role.name == 'Manager'
    
    def test_user_password_hashing(self, app):
        """Test password hashing works correctly."""
        with app.app_context():
            manager_role = Role.query.filter_by(name='Manager').first()
            user = User(username='hash_test', role_id=manager_role.id)
            user.set_password('mysecretpassword')
            
            assert user.password_hash != 'mysecretpassword'
            assert user.check_password('mysecretpassword') is True
            assert user.check_password('wrongpassword') is False
    
    def test_user_roles(self, app):
        """Test user role assignment."""
        with app.app_context():
            engineer_role = Role.query.filter_by(name='Engineer').first()
            user = User(username='role_test', role_id=engineer_role.id)
            db.session.add(user)
            db.session.commit()
            
            assert user.has_role('Engineer') is True
            assert user.has_role('Manager') is False
    
    def test_sensor_data_accepts_floats(self, app):
        """Test SensorData accepts floats."""
        with app.app_context():
            sensor_data = SensorData(
                sensor_name='Test_Sensor',
                value=42.5,
                unit='deg',
                status='OK'
            )
            db.session.add(sensor_data)
            db.session.commit()
            
            retrieved = SensorData.query.first()
            assert retrieved is not None
            assert retrieved.value == 42.5
            assert isinstance(retrieved.value, float)
    
    def test_sensor_data_to_dict(self, app):
        """Test SensorData to_dict method."""
        with app.app_context():
            sensor_data = SensorData(
                sensor_name='Test_Sensor',
                value=100.0,
                unit='RPM',
                status='OK'
            )
            db.session.add(sensor_data)
            db.session.commit()
            
            data_dict = sensor_data.to_dict()
            assert data_dict['sensor_name'] == 'Test_Sensor'
            assert data_dict['value'] == 100.0
            assert data_dict['unit'] == 'RPM'
            assert data_dict['status'] == 'OK'
            assert 'timestamp' in data_dict
    
    def test_role_permissions(self, app):
        """Test role permissions are set correctly."""
        with app.app_context():
            investor_role = Role.query.filter_by(name='Investor').first()
            perms = investor_role.permissions
            
            assert perms is not None
            assert perms.can_view_panel_1 is True
            assert perms.can_view_panel_2 is True
            assert perms.can_view_panel_3 is False
            assert perms.can_export_data is False
            assert perms.can_manage_users is False


class TestAuthentication:
    """Test cases for authentication."""
    
    def test_root_redirects_to_login(self, client):
        """Test root URL redirects to login."""
        response = client.get('/')
        assert response.status_code == 302
        assert '/auth/login' in response.location
    
    def test_login_page_loads(self, client):
        """Test login page loads."""
        response = client.get('/auth/login')
        assert response.status_code == 200
        assert b'login' in response.data.lower()
    
    def test_login_valid_credentials(self, app, client, manager_user):
        """Test login with valid credentials."""
        response = client.post('/auth/login', data={
            'username': 'manager',
            'password': 'testpass'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        assert b'dashboard' in response.data.lower()
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post('/auth/login', data={
            'username': 'nonexistent',
            'password': 'wrongpass'
        }, follow_redirects=True)
        
        assert b'Invalid username or password' in response.data
    
    def test_login_wrong_password(self, app, client, manager_user):
        """Test login with wrong password."""
        response = client.post('/auth/login', data={
            'username': 'manager',
            'password': 'wrongpass'
        }, follow_redirects=True)
        
        assert b'Invalid username or password' in response.data
    
    def test_logout(self, app, client, manager_user):
        """Test logout functionality."""
        client.post('/auth/login', data={
            'username': 'manager',
            'password': 'testpass'
        }, follow_redirects=True)
        
        response = client.get('/auth/logout', follow_redirects=True)
        assert b'logged out' in response.data.lower()
    
    def test_logout_requires_login(self, client):
        """Test logout without being logged in."""
        response = client.get('/auth/logout', follow_redirects=False)
        assert response.status_code == 302
    
    def test_logged_in_user_redirect_from_login(self, app, client, manager_user):
        """Test logged in user is redirected from login page."""
        client.post('/auth/login', data={
            'username': 'manager',
            'password': 'testpass'
        })
        
        response = client.get('/auth/login')
        assert response.status_code == 302
