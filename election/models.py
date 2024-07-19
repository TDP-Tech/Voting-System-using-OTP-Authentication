# election/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
import random, datetime
from django.utils import timezone

class StudentManager(BaseUserManager):
    def create_user(self, student_id, password=None, email=''):
        if not student_id:
            raise ValueError("Students must have a university ID")
        student = self.model(student_id=student_id, email=email)
        student.set_password(password)
        student.save(using=self._db)
        return student

    def create_superuser(self, student_id, password=None, email=''):
        student = self.create_user(student_id, password, email=email)
        student.is_admin = True
        student.save(using=self._db)
        return student
    
    
class Student(AbstractBaseUser, PermissionsMixin):
    student_id = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    fingerprint = models.BinaryField()
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = StudentManager()

    USERNAME_FIELD = 'student_id'
    EMAIL_FIELD = 'email'

    def __str__(self):
        return self.student_id

    @property
    def is_staff(self):
        return self.is_admin

    @property
    def is_superuser(self):
        return self.is_admin

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.otp_created_at = timezone.now()
        self.save()
        return self.otp

    def is_otp_valid(self, otp):
        expiry_time = self.otp_created_at + datetime.timedelta(minutes=10)
        return self.otp == otp and timezone.now() < expiry_time


class Category(models.Model):
    category_name = models.CharField(max_length=100, unique=True)
    voting_start_time = models.DateTimeField(null=True, blank=True)
    voting_end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.category_name

class Candidate(models.Model):
    first_name = models.CharField(max_length=100, blank=False)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=False)
    image = models.ImageField(upload_to='candidates/')
    course = models.CharField(max_length=100)
    level_of_study = models.CharField(max_length=100)
    year_of_study = models.CharField(max_length=50)
    position = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

class Vote(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    
