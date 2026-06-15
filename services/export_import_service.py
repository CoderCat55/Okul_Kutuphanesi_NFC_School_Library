import os
import sqlite3
import shutil
from database import DATABASE_PATH

def export_database(export_path=None):
    """Export the database to a file"""
    if export_path is None:
        export_path = f"library_backup_{int(os.time())}.db"

    # Copy the database file
    shutil.copy2(DATABASE_PATH, export_path)
    return export_path

def import_database(import_path):
    """Import a database file, replacing the current one"""
    if not os.path.exists(import_path):
        raise FileNotFoundError(f"Import file not found: {import_path}")

    # Validate that it's a SQLite database
    if not import_path.endswith('.db'):
        raise ValueError("Import file must be a .db file")

    # Backup current database
    backup_path = f"{DATABASE_PATH}.backup_{int(os.time())}"
    shutil.copy2(DATABASE_PATH, backup_path)

    # Replace current database with imported one
    shutil.copy2(import_path, DATABASE_PATH)

    return True