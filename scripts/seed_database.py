"""
Database seeding script for MTI (Miami Telemetry Interface)

This script initializes the database with:
- 5 default roles (Manager, Engineer, Operator, Investor, Audit)
- Default permissions for each role
- Default admin user (username: admin, password: admin123)

Usage:
    python scripts/seed_database.py
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Role, RolePermission, DEFAULT_PERMISSIONS


def seed_roles():
    """Create the 5 default roles."""
    roles = ['Manager', 'Engineer', 'Operator', 'Investor', 'Audit']
    created = []
    
    for role_name in roles:
        role = Role.query.filter_by(name=role_name).first()
        if role is None:
            role = Role(name=role_name)
            db.session.add(role)
            created.append(role_name)
            print(f"  Created role: {role_name}")
        else:
            print(f"  Role exists: {role_name}")
    
    db.session.commit()
    return created


def seed_permissions():
    """Create default permissions for each role."""
    for role_name, perms in DEFAULT_PERMISSIONS.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            print(f"  ERROR: Role '{role_name}' not found")
            continue
        
        existing = RolePermission.query.filter_by(role_id=role.id).first()
        if existing:
            print(f"  Permissions exist for: {role_name}")
            continue
        
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
        print(f"  Created permissions for: {role_name}")
    
    db.session.commit()


def seed_admin():
    """Create the default admin user with Manager role."""
    manager_role = Role.query.filter_by(name='Manager').first()
    if manager_role is None:
        print("  ERROR: Manager role not found. Run seed_roles first.")
        return None
    
    admin = User.query.filter_by(username='admin').first()
    if admin is None:
        admin = User(username='admin', role_id=manager_role.id)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("  Created admin user (username: admin, password: admin123)")
        return admin
    else:
        print("  Admin user already exists")
        return admin


def seed_demo_users():
    """Create demo users for each role."""
    demo_users = [
        ('engineer1', 'engineer123', 'Engineer'),
        ('operator1', 'operator123', 'Operator'),
        ('investor1', 'investor123', 'Investor'),
        ('auditor1', 'auditor123', 'Audit'),
    ]
    
    for username, password, role_name in demo_users:
        role = Role.query.filter_by(name=role_name).first()
        if role is None:
            print(f"  ERROR: Role '{role_name}' not found")
            continue
        
        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User(username=username, role_id=role.id)
            user.set_password(password)
            db.session.add(user)
            print(f"  Created user: {username} ({role_name})")
        else:
            print(f"  User exists: {username}")
    
    db.session.commit()


def main():
    """Main seeding function."""
    print("=" * 60)
    print("MTI Database Seeding Script")
    print("=" * 60)
    
    app = create_app('default')
    
    with app.app_context():
        # Create all tables
        print("\nCreating database tables...")
        db.create_all()
        print("  Tables created successfully")
        
        # Seed roles
        print("\nSeeding roles...")
        seed_roles()
        
        # Seed permissions
        print("\nSeeding permissions...")
        seed_permissions()
        
        # Seed admin user
        print("\nSeeding admin user...")
        seed_admin()
        
        # Seed demo users
        print("\nSeeding demo users...")
        seed_demo_users()
        
        print("\n" + "=" * 60)
        print("Database seeding complete!")
        print("=" * 60)
        print("\nDefault credentials:")
        print("  Admin:    admin / admin123")
        print("  Engineer: engineer1 / engineer123")
        print("  Operator: operator1 / operator123")
        print("  Investor: investor1 / investor123")
        print("  Auditor:  auditor1 / auditor123")
        print("\nDefault permissions (most restrictive to least):")
        print("  Investor: Panels 1-2 only, no export")
        print("  Audit:    Panels 1-3, export + access logs")
        print("  Operator: All panels, no export")
        print("  Engineer: All panels, export + edit")
        print("  Manager:  Full access + admin")


if __name__ == '__main__':
    main()
