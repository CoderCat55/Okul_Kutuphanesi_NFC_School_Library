from database import get_db_connection
import uuid
from datetime import datetime
import os

class Student:
    @staticmethod
    def create(student_number, name, class_name=None):
        print(f"Creating student with DB_PATH: {os.environ.get('DATABASE_PATH', 'NOT SET')}")  # Debug
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Check if student already exists
            cursor.execute('SELECT COUNT(*) FROM students WHERE student_number = ?', (student_number,))
            count = cursor.fetchone()[0]
            print(f"Found {count} existing students with student_number {student_number}")  # Debug
            if count > 0:
                cursor.execute('SELECT * FROM students WHERE student_number = ?', (student_number,))
                rows = cursor.fetchall()
                print(f"Existing rows: {rows}")  # Debug
            print(f"About to execute INSERT")  # Debug
            cursor.execute(
                'INSERT INTO students (student_number, name, class) VALUES (?, ?, ?)',
                (student_number, name, class_name)
            )
            print(f"About to commit")  # Debug
            conn.commit()
            print(f"About to find_by_id with lastrowid: {cursor.lastrowid}")  # Debug
            result = Student.find_by_id(cursor.lastrowid)
            print(f"Student.create returning: {result}")  # Debug
            return result

    @staticmethod
    def find_by_id(student_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
            row = cursor.fetchone()
            if row:
                return Student(
                    id=row['id'],
                    student_number=row['student_number'],
                    name=row['name'],
                    class_name=row['class'],
                    created_at=row['created_at']
                )
            return None

    @staticmethod
    def find_by_student_number(student_number):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM students WHERE student_number = ?', (student_number,))
            row = cursor.fetchone()
            if row:
                return Student(
                    id=row['id'],
                    student_number=row['student_number'],
                    name=row['name'],
                    class_name=row['class'],
                    created_at=row['created_at']
                )
            return None

    def __init__(self, id, student_number, name, class_name=None, created_at=None):
        self.id = id
        self.student_number = student_number
        self.name = name
        self.class_name = class_name
        self.created_at = created_at

    def __repr__(self):
        return f"<Student {self.id}: {self.student_number} - {self.name}>"

class Resource:
    @staticmethod
    def create(uuid, title, author=None, language=None, shelf_location=None,
               resource_type='physical', tags=None, file_path=None, nfc_tag=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO resources
                   (uuid, title, author, language, shelf_location, resource_type, tags, file_path, nfc_tag)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (uuid, title, author, language, shelf_location, resource_type, tags, file_path, nfc_tag)
            )
            conn.commit()
            return Resource.find_by_id(cursor.lastrowid)

    @staticmethod
    def find_by_id(resource_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM resources WHERE id = ?', (resource_id,))
            row = cursor.fetchone()
            if row:
                return Resource(
                    id=row['id'],
                    uuid=row['uuid'],
                    title=row['title'],
                    author=row['author'],
                    language=row['language'],
                    shelf_location=row['shelf_location'],
                    resource_type=row['resource_type'],
                    tags=row['tags'],
                    file_path=row['file_path'],
                    nfc_tag=row['nfc_tag'],
                    created_at=row['created_at'],
                    is_available=bool(row['is_available'])
                )
            return None

    @staticmethod
    def find_by_uuid(uuid):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM resources WHERE uuid = ?', (uuid,))
            row = cursor.fetchone()
            if row:
                return Resource(
                    id=row['id'],
                    uuid=row['uuid'],
                    title=row['title'],
                    author=row['author'],
                    language=row['language'],
                    shelf_location=row['shelf_location'],
                    resource_type=row['resource_type'],
                    tags=row['tags'],
                    file_path=row['file_path'],
                    nfc_tag=row['nfc_tag'],
                    created_at=row['created_at'],
                    is_available=bool(row['is_available'])
                )
            return None

    @staticmethod
    def find_by_nfc_tag(nfc_tag):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM resources WHERE nfc_tag = ?', (nfc_tag,))
            row = cursor.fetchone()
            if row:
                return Resource(
                    id=row['id'],
                    uuid=row['uuid'],
                    title=row['title'],
                    author=row['author'],
                    language=row['language'],
                    shelf_location=row['shelf_location'],
                    resource_type=row['resource_type'],
                    tags=row['tags'],
                    file_path=row['file_path'],
                    nfc_tag=row['nfc_tag'],
                    created_at=row['created_at'],
                    is_available=bool(row['is_available'])
                )
            return None

    def __init__(self, id, uuid, title, author=None, language=None, shelf_location=None,
                 resource_type='physical', tags=None, file_path=None, nfc_tag=None,
                 created_at=None, is_available=True):
        self.id = id
        self.uuid = uuid
        self.title = title
        self.author = author
        self.language = language
        self.shelf_location = shelf_location
        self.resource_type = resource_type
        self.tags = tags
        self.file_path = file_path
        self.nfc_tag = nfc_tag
        self.created_at = created_at
        self.is_available = is_available

    def __repr__(self):
        return f"<Resource {self.id}: {self.title} ({self.uuid})>"

class Transaction:
    @staticmethod
    def create(student_id, resource_id, transaction_type, notes=None):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO transactions (student_id, resource_id, transaction_type, notes) VALUES (?, ?, ?, ?)',
                (student_id, resource_id, transaction_type, notes)
            )
            conn.commit()
            return Transaction.find_by_id(cursor.lastrowid)

    @staticmethod
    def find_by_id(transaction_id):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,))
            row = cursor.fetchone()
            if row:
                return Transaction(
                    id=row['id'],
                    student_id=row['student_id'],
                    resource_id=row['resource_id'],
                    transaction_type=row['transaction_type'],
                    timestamp=row['timestamp'],
                    notes=row['notes']
                )
            return None

    def __init__(self, id, student_id, resource_id, transaction_type, timestamp=None, notes=None):
        self.id = id
        self.student_id = student_id
        self.resource_id = resource_id
        self.transaction_type = transaction_type
        self.timestamp = timestamp
        self.notes = notes

    def __repr__(self):
        return f"<Transaction {self.id}: {self.transaction_type} for student {self.student_id} resource {self.resource_id}>"