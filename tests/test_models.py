import unittest
from models import Student

class TestStudentModel(unittest.TestCase):
    def test_student_creation(self):
        # Test that we can create a student instance
        student = Student(id=1, student_number="S12345", name="John Doe", class_="10A")
        self.assertEqual(student.id, 1)
        self.assertEqual(student.student_number, "S12345")
        self.assertEqual(student.name, "John Doe")
        self.assertEqual(student.class_, "10A")

if __name__ == '__main__':
    unittest.main()