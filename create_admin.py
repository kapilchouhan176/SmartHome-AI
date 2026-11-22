"""
create_admin.py
Optional: creates an extra administrator from the terminal.
The first admin is normally created automatically from ADMIN_* values in .env.

    python3 create_admin.py
"""
import getpass

from app import create_app
from services.admin_setup import create_admin


# Asks for the admin's details and saves the account.
def main():
    print("=== Create SmartHome AI Administrator ===")
    name = input("Admin name: ").strip()
    email = input("Admin email: ").strip()
    password = getpass.getpass("Password (min 8 characters): ")
    if password != getpass.getpass("Confirm password: "):
        return print("Error: passwords do not match.")
    with create_app().app_context():
        ok, message = create_admin(name, email, password)
    print(message if ok else f"Error: {message}")


if __name__ == "__main__":
    main()
