"""Compatibility entry point; initializes only, never seeds or resets data."""

from app import create_app
from app.commands import init_database

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        init_database()
    print("Database ready. Run the explicit seed-demo command for demonstration data.")
