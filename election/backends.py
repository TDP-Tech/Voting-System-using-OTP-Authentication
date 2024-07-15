# election/backends.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from .models import Student

class StudentBackend(BaseBackend):
    def authenticate(self, request, student_id=None, password=None):
        try:
            student = Student.objects.get(student_id=student_id)
            if check_password(password, student.password):
                return student
        except Student.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return Student.objects.get(pk=user_id)
        except Student.DoesNotExist:
            return None
