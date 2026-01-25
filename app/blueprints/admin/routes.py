"""
Admin routes for user management.
"""
from functools import wraps
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import admin_bp
from ...extensions import db
from ...models import User, Role, RolePermission


def manager_required(f):
    """Decorator to require Manager role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.can_access_admin():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard.grid_view'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/users')
@login_required
@manager_required
def users():
    """Display user management page."""
    users = User.query.all()
    roles = Role.query.all()
    return render_template('admin/create_user.html', users=users, roles=roles)


@admin_bp.route('/users/create', methods=['POST'])
@login_required
@manager_required
def create_user():
    """Create a new user."""
    username = request.form.get('username')
    password = request.form.get('password')
    role_id = request.form.get('role_id')

    if not username or not password or not role_id:
        flash('All fields are required.', 'error')
        return redirect(url_for('admin.users'))

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('Username already exists.', 'error')
        return redirect(url_for('admin.users'))

    user = User(username=username, role_id=int(role_id))
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    flash(f'User "{username}" created successfully.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@manager_required
def delete_user(user_id):
    """Delete a user."""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete yourself.', 'error')
        return redirect(url_for('admin.users'))

    username = user.username
    db.session.delete(user)
    db.session.commit()

    flash(f'User "{username}" deleted successfully.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@manager_required
def reset_password(user_id):
    """Reset a user's password."""
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')

    if not new_password:
        flash('New password is required.', 'error')
        return redirect(url_for('admin.users'))

    user.set_password(new_password)
    db.session.commit()

    flash(f'Password for "{user.username}" reset successfully.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/permissions')
@login_required
@manager_required
def permissions():
    """Display permission management page."""
    roles = Role.query.all()
    return render_template('admin/permissions.html', roles=roles)


@admin_bp.route('/permissions/<int:role_id>/update', methods=['POST'])
@login_required
@manager_required
def update_permissions(role_id):
    """Update permissions for a role."""
    role = Role.query.get_or_404(role_id)
    
    # Get or create permission record
    perm = RolePermission.query.filter_by(role_id=role_id).first()
    if not perm:
        perm = RolePermission(role_id=role_id)
        db.session.add(perm)
    
    # Update permissions from form checkboxes
    perm.can_view_panel_1 = 'can_view_panel_1' in request.form
    perm.can_view_panel_2 = 'can_view_panel_2' in request.form
    perm.can_view_panel_3 = 'can_view_panel_3' in request.form
    perm.can_view_panel_4 = 'can_view_panel_4' in request.form
    perm.can_export_data = 'can_export_data' in request.form
    perm.can_edit_data = 'can_edit_data' in request.form
    perm.can_manage_users = 'can_manage_users' in request.form
    perm.can_view_access_logs = 'can_view_access_logs' in request.form
    
    db.session.commit()
    
    flash(f'Permissions for "{role.name}" updated successfully.', 'success')
    return redirect(url_for('admin.permissions'))
