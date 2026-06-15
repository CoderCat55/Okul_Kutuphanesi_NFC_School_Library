import unittest
import tempfile
import os
from database import init_db

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        os.environ['DATABASE_PATH'] = self.db_path

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_database_initialization(self):
        conn = init_db()
        self.assertIsNotNone(conn)
        conn.close()