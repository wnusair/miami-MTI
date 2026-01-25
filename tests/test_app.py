"""
Unit tests for MTI (Miami Telemetry Interface)

Run tests with: pytest tests/ -v
"""

import pytest
from app import create_app, db
from app.models import User, Role, SensorData


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        # Seed roles
        roles = ['Manager', 'Engineer', 'Operator', 'Investor', 'Audit']
        for role_name in roles:
            role = Role(name=role_name)
            db.session.add(role)
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


class TestSensorDataModel:
    """Test cases for SensorData model."""
    
    def test_sensor_data_accepts_floats(self, app):
        """Test Case 1: Ensure SensorData accepts floats."""
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
    
    def test_sensor_data_rejects_strings(self, app):
        """Test Case 1: Ensure SensorData rejects strings for value field."""
        with app.app_context():
            with pytest.raises((ValueError, TypeError, Exception)):
                # SQLAlchemy should raise an error when trying to store a string
                sensor_data = SensorData(
                    sensor_name='Test_Sensor',
                    value='not_a_float',  # This should fail
                    unit='deg',
                    status='OK'
                )
                db.session.add(sensor_data)
                db.session.commit()
    
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


class TestRoleAccess:
    """Test cases for role-based access control."""
    
    def test_investor_cannot_access_admin(self, app, client):
        """Test Case 2: Ensure Investor role cannot access /admin."""
        with app.app_context():
            # Create an investor user
            investor_role = Role.query.filter_by(name='Investor').first()
            investor = User(username='investor_test', role_id=investor_role.id)
            investor.set_password('test123')
            db.session.add(investor)
            db.session.commit()
        
        # Login as investor
        client.post('/auth/login', data={
            'username': 'investor_test',
            'password': 'test123'
        }, follow_redirects=True)
        
        # Try to access admin page
        response = client.get('/admin/users', follow_redirects=True)
        
        # Should be redirected or denied
        # The flash message indicates access denied
        assert b'Access denied' in response.data or b'Manager role required' in response.data
    
    def test_manager_can_access_admin(self, app, client):
        """Test that Manager role can access /admin."""
        with app.app_context():
            # Create a manager user
            manager_role = Role.query.filter_by(name='Manager').first()
            manager = User(username='manager_test', role_id=manager_role.id)
            manager.set_password('test123')
            db.session.add(manager)
            db.session.commit()
        
        # Login as manager
        client.post('/auth/login', data={
            'username': 'manager_test',
            'password': 'test123'
        }, follow_redirects=True)
        
        # Try to access admin page
        response = client.get('/admin/users')
        
        # Should be successful (200) or OK
        assert response.status_code == 200


class TestExportAPI:
    """Test cases for data export functionality."""
    
    def test_xlsx_export_returns_200(self, app, client):
        """Test Case 3: Ensure .xlsx export returns HTTP 200."""
        with app.app_context():
            # Create a user to authenticate
            manager_role = Role.query.filter_by(name='Manager').first()
            user = User(username='export_test', role_id=manager_role.id)
            user.set_password('test123')
            db.session.add(user)
            
            # Add some test data
            sensor_data = SensorData(
                sensor_name='Test_Sensor',
                value=50.0,
                unit='deg',
                status='OK'
            )
            db.session.add(sensor_data)
            db.session.commit()
        
        # Login
        client.post('/auth/login', data={
            'username': 'export_test',
            'password': 'test123'
        }, follow_redirects=True)
        
        # Request export
        response = client.get('/api/export')
        
        # Check response
        assert response.status_code == 200
    
    def test_xlsx_export_correct_mime_type(self, app, client):
        """Test Case 3: Ensure .xlsx export returns correct MIME type."""
        with app.app_context():
            # Create a user
            manager_role = Role.query.filter_by(name='Manager').first()
            user = User(username='mime_test', role_id=manager_role.id)
            user.set_password('test123')
            db.session.add(user)
            db.session.commit()
        
        # Login
        client.post('/auth/login', data={
            'username': 'mime_test',
            'password': 'test123'
        }, follow_redirects=True)
        
        # Request export
        response = client.get('/api/export')
        
        # Check MIME type
        expected_mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert response.content_type == expected_mime


class TestAuthentication:
    """Test cases for authentication."""
    
    def test_login_valid_credentials(self, app, client):
        """Test login with valid credentials."""
        with app.app_context():
            manager_role = Role.query.filter_by(name='Manager').first()
            user = User(username='valid_user', role_id=manager_role.id)
            user.set_password('valid_pass')
            db.session.add(user)
            db.session.commit()
        
        response = client.post('/auth/login', data={
            'username': 'valid_user',
            'password': 'valid_pass'
        }, follow_redirects=True)
        
        # Should redirect to dashboard
        assert b'Dashboard' in response.data or b'dashboard' in response.data.lower()
    
    def test_login_invalid_credentials(self, app, client):
        """Test login with invalid credentials."""
        response = client.post('/auth/login', data={
            'username': 'nonexistent',
            'password': 'wrongpass'
        }, follow_redirects=True)
        
        # Should show error message
        assert b'Invalid username or password' in response.data
    
    def test_logout(self, app, client):
        """Test logout functionality."""
        with app.app_context():
            manager_role = Role.query.filter_by(name='Manager').first()
            user = User(username='logout_user', role_id=manager_role.id)
            user.set_password('test123')
            db.session.add(user)
            db.session.commit()
        
        # Login first
        client.post('/auth/login', data={
            'username': 'logout_user',
            'password': 'test123'
        }, follow_redirects=True)
        
        # Now logout
        response = client.get('/auth/logout', follow_redirects=True)
        
        # Should show logged out message
        assert b'logged out' in response.data.lower()


class TestUserModel:
    """Test cases for User model."""
    
    def test_password_hashing(self, app):
        """Test password hashing works correctly."""
        with app.app_context():
            manager_role = Role.query.filter_by(name='Manager').first()
            user = User(username='hash_test', role_id=manager_role.id)
            user.set_password('mysecretpassword')
            
            # Password should be hashed, not stored as plain text
            assert user.password_hash != 'mysecretpassword'
            
            # Check password should work
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
            assert user.can_access_admin() is False
