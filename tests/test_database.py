import unittest
import tempfile
import os
import importlib

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        os.environ['DATABASE_PATH'] = self.db_path
        # Import the database module after setting the environment variable
        global database
        import database
        importlib.reload(database)
        self.init_db = database.init_db

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_database_initialization(self):
        """Test that the database is initialized with correct tables and constraints."""
        conn = None
        try:
            conn = self.init_db()
            self.assertIsNotNone(conn)

            # Check that tables exist
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            # Remove internal SQLite tables
            tables.discard('sqlite_sequence')
            expected_tables = {'students', 'resources', 'transactions', 'activity_log'}
            self.assertEqual(tables, expected_tables)

            # Check that resources table has the CHECK constraint on resource_type
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='resources'")
            sql = cursor.fetchone()[0]
            self.assertIn("CHECK (resource_type IN ('physical', 'digital'))", sql)

            # Check that transactions table has the CHECK constraint on transaction_type
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='transactions'")
            sql = cursor.fetchone()[0]
            self.assertIn("CHECK (transaction_type IN ('checkout', 'return'))", sql)
        finally:
            if conn:
                conn.close()