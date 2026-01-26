"""Reset or regenerate user passwords.

Usage:
  # Reset a single user to a specific password
  python scripts/reset_passwords.py --user alice --password NewPass123!

  # Reset all users to the same password (requires confirmation)
  python scripts/reset_passwords.py --all --password Default123!

  # Reset all users to random passwords and print them
  python scripts/reset_passwords.py --all --random --length 16

This script uses the app factory to get a Flask app/app context and updates
the database via the SQLAlchemy `db` object.
"""
import argparse
import secrets
import string
import sys
from pathlib import Path
import os

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

if not os.environ.get('SECRET_KEY'):
    temp_key = secrets.token_hex(32)
    os.environ['SECRET_KEY'] = temp_key
    print('NOTE: SECRET_KEY was not set; using a generated temporary SECRET_KEY for this run.')

from app import create_app
from app.extensions import db
from app.models import User


def generate_password(length=16):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def reset_passwords(users, new_passwords):
    """Apply new_passwords to the provided user objects and commit.

    NOTE: This function expects to be called while an application context
    is active (so that `db.session` is the same session used to load `users`).
    """
    for user, pwd in zip(users, new_passwords):
        user.set_password(pwd)
    db.session.commit()


def main():
    parser = argparse.ArgumentParser(description='Reset user passwords')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--all', action='store_true', help='Reset passwords for all users')
    group.add_argument('--user', help='Username to reset')

    parser.add_argument('--password', help='New password to set (use with --all or --user)')
    parser.add_argument('--random', action='store_true', help='Generate random password(s)')
    parser.add_argument('--length', type=int, default=16, help='Length of generated passwords')
    parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')

    args = parser.parse_args()

    if not args.password and not args.random:
        print('Either --password or --random is required.')
        parser.print_help()
        sys.exit(1)

    app = create_app()

    with app.app_context():
        if args.all:
            users = User.query.order_by(User.id).all()
            if not users:
                print('No users found in database.')
                return

            if not args.yes:
                confirm = input(f"About to reset passwords for {len(users)} users. Continue? [y/N]: ")
                if confirm.lower() not in ('y', 'yes'):
                    print('Aborted.')
                    return

            new_passwords = []
            if args.random:
                for _ in users:
                    new_passwords.append(generate_password(args.length))
            else:
                new_passwords = [args.password] * len(users)

            reset_passwords(users, new_passwords)

            # Print results
            for u, p in zip(users, new_passwords):
                print(f'{u.username}: {p}')

        else:
            user = User.query.filter_by(username=args.user).first()
            if not user:
                print(f'User not found: {args.user}')
                return

            if args.random:
                pwd = generate_password(args.length)
            else:
                pwd = args.password

            if not args.yes:
                confirm = input(f"Reset password for '{user.username}'? [y/N]: ")
                if confirm.lower() not in ('y', 'yes'):
                    print('Aborted.')
                    return

            reset_passwords([user], [pwd])
            print(f'{user.username}: {pwd}')


if __name__ == '__main__':
    main()
