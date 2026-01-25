"""
User and Role models for authentication and authorization.
"""
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from ..extensions import db


class Role(db.Model):
    """Role model for user authorization."""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return f'<Role {self.name}>'

    def get_permissions(self):
        """Get the permission object for this role."""
        return self.permissions


class User(UserMixin, db.Model):
    """User model for authentication."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check the provided password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        """Check if user has a specific role."""
        return self.role and self.role.name == role_name

    def get_permissions(self):
        """Get the user's permissions based on their role."""
        if self.role and self.role.permissions:
            return self.role.permissions
        return None

    def can_view_panel(self, panel_num):
        """Check if user can view a specific panel (1-4)."""
        perms = self.get_permissions()
        if not perms:
            return False
        return getattr(perms, f'can_view_panel_{panel_num}', False)

    def can_export(self):
        """Check if user can export data."""
        perms = self.get_permissions()
        return perms.can_export_data if perms else False

    def can_edit(self):
        """Check if user can edit/write data."""
        perms = self.get_permissions()
        return perms.can_edit_data if perms else False

    def can_access_admin(self):
        """Check if user can access admin panel."""
        perms = self.get_permissions()
        return perms.can_manage_users if perms else False

    def can_view_logs(self):
        """Check if user can view access logs."""
        perms = self.get_permissions()
        return perms.can_view_access_logs if perms else False

    def __repr__(self):
        return f'<User {self.username}>'
