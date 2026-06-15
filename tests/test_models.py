import unittest
import tempfile
import os
import uuid
from models import Student, Resource, Transaction
from database import init_db, get_db_connection

class TestModels(unittest.TestCase):
    def setUp(self):
        self.db_path = os.path.join(tempfile.gettempdir(), f'test_db_{os.getpid()}_{id(self)}.db')
        print(f"Before setting env: db_path exists = {os.path.exists(self.db_path)}")  # Debug
        if os.path.exists(self.db_path):
            print(f"WARNING: Database file already exists at {self.db_path}")  # Debug
            # Let's see what's in it
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM students')
            count = cursor.fetchone()[0]
            print(f"Existing file has {count} students")
            if count > 0:
                cursor.execute('SELECT * FROM students')
                rows = cursor.fetchall()
                for i, row in enumerate(rows):
                    print(f"  Existing row {i}: {dict(row)}")
            conn.close()

        print(f"About to set DATABASE_PATH to {self.db_path}")  # Debug
        print(f"Current DATABASE_PATH in env: {os.environ.get('DATABASE_PATH', 'NOT SET')}")  # Debug
        os.environ['DATABASE_PATH'] = self.db_path
        print(f"After setting DATABASE_PATH: {os.environ.get('DATABASE_PATH', 'NOT SET')}")  # Debug
        db_conn = init_db()  # Initialize tables
        # Check what's in the students table after init
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM students')
            count = cursor.fetchone()[0]
            print(f"After init_db: {count} students in table")  # Debug
            if count > 0:
                cursor.execute('SELECT * FROM students')
                rows = cursor.fetchall()
                print(f"Rows in students table:")  # Debug
                for i, row in enumerate(rows):
                    print(f"  Row {i}: dict(row) = {dict(row)}")  # Debug
        # Close the connection returned by init_db()
        db_conn.close()

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_student_creation(self):
        student = Student.create("12345", "John Doe", "10A")
        self.assertIsNotNone(student.id)
        self.assertEqual(student.student_number, "12345")
        self.assertEqual(student.name, "John Doe")
        self.assertEqual(student.class_name, "10A")

    def test_student_find_by_number(self):
        Student.create("12345", "John Doe", "10A")
        student = Student.find_by_student_number("12345")
        self.assertIsNotNone(student)
        self.assertEqual(student.student_number, "12345")
        self.assertEqual(student.name, "John Doe")

    def test_resource_creation(self):
        test_uuid = str(uuid.uuid4())
        resource = Resource.create(test_uuid, "Test Book", "Author Name", "English", "Shelf A1")
        self.assertIsNotNone(resource.id)
        self.assertEqual(resource.uuid, test_uuid)
        self.assertEqual(resource.title, "Test Book")
        self.assertEqual(resource.author, "Author Name")
        self.assertEqual(resource.language, "English")
        self.assertEqual(resource.shelf_location, "Shelf A1")
        self.assertTrue(resource.is_available)

    def test_resource_find_by_uuid(self):
        test_uuid = str(uuid.uuid4())
        Resource.create(test_uuid, "Test Book", "Author Name", "English", "Shelf A1")
        resource = Resource.find_by_uuid(test_uuid)
        self.assertIsNotNone(resource)
        self.assertEqual(resource.uuid, test_uuid)
        self.assertEqual(resource.title, "Test Book")

    def test_transaction_creation(self):
        # Create a student and resource first
        student = Student.create("12345", "John Doe", "10A")
        test_uuid = str(uuid.uuid4())
        resource = Resource.create(test_uuid, "Test Book", "Author Name", "English", "Shelf A1")

        # Create a transaction
        transaction = Transaction.create(student.id, resource.id, "checkout", "For home reading")
        self.assertIsNotNone(transaction.id)
        self.assertEqual(transaction.student_id, student.id)
        self.assertEqual(transaction.resource_id, resource.id)
        self.assertEqual(transaction.transaction_type, "checkout")
        self.assertEqual(transaction.notes, "For home reading")

if __name__ == '__main__':
    unittest.main()