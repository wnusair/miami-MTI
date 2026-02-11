"""
Test cases for user permissions and role-based access control.
"""

import pytest
from app import create_app, db
from app.models import User, Role, RolePermission, DEFAULT_PERMISSIONS


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


class TestRolePermissions:
    """Test role-based permission system."""
    
    def test_investor_permissions(self, app):
        """Test Investor role has correct permissions."""
        with app.app_context():
            role = Role.query.filter_by(name='Investor').first()
            user = User(username='investor', role_id=role.id)
            user.set_password('test')
            db.session.add(user)
            db.session.commit()
            
            assert user.can_view_panel(1) is True
            assert user.can_view_panel(2) is True
            assert user.can_view_panel(3) is False
            assert user.can_view_panel(4) is False
            assert user.can_export() is False
            assert user.can_edit() is False
            assert user.can_access_admin() is False
            assert user.can_view_logs() is False
    
    def test_audit_permissions(self, app):
        """Test Audit role has correct permissions."""
        with app.app_context():
            role = Role.query.filter_by(name='Audit').first()
            user = User(username='auditor', role_id=role.id)
            user.set_password('test')
            db.session.add(user)
            db.session.commit()
            
            assert user.can_view_panel(1) is True
            assert user.can_view_panel(2) is True
            assert user.can_view_panel(3) is True
            assert user.can_view_panel(4) is False
            assert user.can_export() is True
            assert user.can_edit() is False
            assert user.can_access_admin() is False
            assert user.can_view_logs() is True
    
    def test_operator_permissions(self, app):
        """Test Operator role has correct permissions."""
        with app.app_context():
            role = Role.query.filter_by(name='Operator').first()
            user = User(username='operator', role_id=role.id)
            user.set_password('test')
            db.session.add(user)
            db.session.commit()
            
            assert user.can_view_panel(1) is True
            assert user.can_view_panel(2) is True
            assert user.can_view_panel(3) is True
            assert user.can_view_panel(4) is True
            assert user.can_export() is False
            assert user.can_edit() is False
            assert user.can_access_admin() is False
            assert user.can_view_logs() is False
    
    def test_engineer_permissions(self, app):
        """Test Engineer role has correct permissions."""
        with app.app_context():
            role = Role.query.filter_by(name='Engineer').first()
            user = User(username='engineer', role_id=role.id)
            user.set_password('test')
            db.session.add(user)
            db.session.commit()
            
            assert user.can_view_panel(1) is True
            assert user.can_view_panel(2) is True
            assert user.can_view_panel(3) is True
            assert user.can_view_panel(4) is True
            assert user.can_export() is True
            assert user.can_edit() is True
            assert user.can_access_admin() is False
            assert user.can_view_logs() is False
    
    def test_manager_permissions(self, app):
        """Test Manager role has correct permissions."""
        with app.app_context():
            role = Role.query.filter_by(name='Manager').first()
            user = User(username='manager', role_id=role.id)
            user.set_password('test')
            db.session.add(user)
            db.session.commit()
            
            assert user.can_view_panel(1) is True
            assert user.can_view_panel(2) is True
            assert user.can_view_panel(3) is True
            assert user.can_view_panel(4) is True
            assert user.can_export() is True
            assert user.can_edit() is True
            assert user.can_access_admin() is True
            assert user.can_view_logs() is True
    
    def test_permission_to_dict(self, app):
        """Test permission to_dict method."""
        with app.app_context():
            role = Role.query.filter_by(name='Manager').first()
            perms = role.permissions
            
            perm_dict = perms.to_dict()
            
            assert isinstance(perm_dict, dict)
            assert 'can_view_panel_1' in perm_dict
            assert 'can_export_data' in perm_dict
            assert 'can_manage_users' in perm_dict
            assert perm_dict['can_manage_users'] is True
    
    def test_role_get_permissions(self, app):
        """Test role get_permissions method."""
        with app.app_context():
            role = Role.query.filter_by(name='Engineer').first()
            perms = role.get_permissions()
            
            assert perms is not None
            assert perms.can_export_data is True
            assert perms.can_edit_data is True
    
    def test_user_without_permissions(self, app):
        """Test user without permissions returns False for permission checks."""
        with app.app_context():
            role = Role(name='TestRole')
            db.session.add(role)
            db.session.commit()
            
            user = User(username='testuser', role_id=role.id)
            user.set_password('test')
            db.session.add(user)
            db.session.commit()
            
            assert user.can_view_panel(1) is False
            assert user.can_export() is False
            assert user.can_access_admin() is False


class TestAccessControl:
    """Test access control enforcement."""
    
    def test_investor_cannot_export(self, app):
        """Test Investor cannot export data."""
        with app.app_context():
            role = Role.query.filter_by(name='Investor').first()
            user = User(username='investor', role_id=role.id)
            user.set_password('test')
            db.session.add(user)
            db.session.commit()
            
            client = app.test_client()
            client.post('/auth/login', data={
                'username': 'investor',
                'password': 'test'
            })
            
            response = client.get('/api/export')
            assert response.status_code == 403
    
    def test_investor_cannot_access_admin(self, app):
        """Test Investor cannot access admin panel."""
        with app.app_context():
            role = Role.query.filter_by(name='Investor').first()
            user = User(username='investor', role_id=role.id)
            user.set_password('test')
            db.session.add(user)
            db.session.commit()
            
            client = app.test_client()
            client.post('/auth/login', data={
                'username': 'investor',
                'password': 'test'
            })
            
            response = client.get('/admin/users', follow_redirects=True)
            assert b'Access denied' in response.data
    
    def test_engineer_can_export(self, app):
        """Test Engineer can export data."""
        with app.app_context():
            role = Role.query.filter_by(name='Engineer').first()
            user = User(username='engineer', role_id=role.id)
            user.set_password('test')
            db.session.add(user)
            db.session.commit()
            
            client = app.test_client()
            client.post('/auth/login', data={
                'username': 'engineer',
                'password': 'test'
            })
            
            response = client.get('/api/export')
            assert response.status_code == 200
    
    def test_engineer_cannot_access_admin(self, app):
        """Test Engineer cannot access admin panel."""
        with app.app_context():
            role = Role.query.filter_by(name='Engineer').first()
            user = User(username='engineer', role_id=role.id)
            user.set_password('test')
            db.session.add(user)
            db.session.commit()
            
            client = app.test_client()
            client.post('/auth/login', data={
                'username': 'engineer',
                'password': 'test'
            })
            
            response = client.get('/admin/users', follow_redirects=True)
            assert b'Access denied' in response.data
    
    def test_manager_can_access_everything(self, app):
        """Test Manager can access all areas."""
        with app.app_context():
            role = Role.query.filter_by(name='Manager').first()
            user = User(username='manager', role_id=role.id)
            user.set_password('test')
            db.session.add(user)
            db.session.commit()
            
            client = app.test_client()
            client.post('/auth/login', data={
                'username': 'manager',
                'password': 'test'
            })
            
            response = client.get('/admin/users')
            assert response.status_code == 200
            
            response = client.get('/api/export')
            assert response.status_code == 200
