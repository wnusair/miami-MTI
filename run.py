"""
Application entry point for MTI (Miami Telemetry Interface).
"""
import os
from app import create_app, db
from app.models import User, Role, SensorData, RolePermission

app = create_app(os.environ.get('FLASK_CONFIG') or 'default')


@app.shell_context_processor
def make_shell_context():
    """Make database models available in flask shell."""
    return dict(db=db, User=User, Role=Role, SensorData=SensorData, RolePermission=RolePermission)


@app.cli.command()
def seed_roles():
    """Seed the database with default roles."""
    roles = ['Manager', 'Engineer', 'Operator', 'Investor', 'Audit']
    for role_name in roles:
        role = Role.query.filter_by(name=role_name).first()
        if role is None:
            role = Role(name=role_name)
            db.session.add(role)
            print(f'Added role: {role_name}')
        else:
            print(f'Role already exists: {role_name}')
    db.session.commit()
    print('Role seeding complete.')


@app.cli.command()
def seed_admin():
    """Create a default admin user (Manager role)."""
    manager_role = Role.query.filter_by(name='Manager').first()
    if manager_role is None:
        print('Error: Manager role not found. Run seed_roles first.')
        return
    
    admin = User.query.filter_by(username='admin').first()
    if admin is None:
        admin = User(username='admin', role_id=manager_role.id)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('Created admin user (username: admin, password: admin123)')
    else:
        print('Admin user already exists.')


if __name__ == '__main__':
    app.run(debug=True)
