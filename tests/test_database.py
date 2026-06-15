import sys
sys.path.insert(0, '.')

import pytest
from database import init_db, get_db_connection

def test_database_connection():
    # Initialize the database
    init_db()
    # Get a connection
    with get_db_connection() as conn:
        assert conn is not None