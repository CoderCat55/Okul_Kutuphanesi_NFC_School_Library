class Student:
    def __init__(self, id=None, student_number=None, name=None, class_=None, created_at=None):
        self.id = id
        self.student_number = student_number
        self.name = name
        self.class_ = class_
        self.created_at = created_at

    def __repr__(self):
        return f"<Student {self.id}: {self.name}>"

class Resource:
    def __init__(self, id=None, uuid=None, title=None, author=None, language=None, shelf_location=None, resource_type=None, tags=None, file_path=None, created_at=None, is_available=None):
        self.id = id
        self.uuid = uuid
        self.title = title
        self.author = author
        self.language = language
        self.shelf_location = shelf_location
        self.resource_type = resource_type
        self.tags = tags
        self.file_path = file_path
        self.created_at = created_at
        self.is_available = is_available

    def __repr__(self):
        return f"<Resource {self.id}: {self.title}>"

class Transaction:
    def __init__(self, id=None, student_id=None, resource_id=None, transaction_type=None, timestamp=None, notes=None):
        self.id = id
        self.student_id = student_id
        self.resource_id = resource_id
        self.transaction_type = transaction_type
        self.timestamp = timestamp
        self.notes = notes

    def __repr__(self):
        return f"<Transaction {self.id}: {self.transaction_type}>"