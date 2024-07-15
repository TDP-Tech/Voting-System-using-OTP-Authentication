from .models import Student  # Adjust the import path as per your project structure

def get_user_public_key(student_id):
    student = Student.objects.get(student_id=student_id)
    return student.public_key  # Replace with the actual field name where you store the public key
