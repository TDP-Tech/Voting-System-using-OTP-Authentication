# election/forms.py
from django import forms
from .models import Student
from django.core.exceptions import ValidationError


class LoginForm(forms.Form):
    student_id = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)

class VoteForm(forms.Form):
    candidate = forms.CharField(max_length=100)

class RegistrationForm(forms.ModelForm):
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    is_admin = forms.BooleanField(label='Is Admin', required=False)
    is_staff = forms.BooleanField(label='Is Staff', required=False)
    is_superuser = forms.BooleanField(label='Is Superuser', required=False)
    
    class Meta:
        model = Student
        fields = ['student_id', 'email', 'password1', 'password2', 'is_admin', 'is_staff', 'is_superuser']
        widgets = {
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        if Student.objects.filter(student_id=student_id).exists():
            raise ValidationError("A user with this registration number already exists.")
        return student_id

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Student.objects.filter(email=email).exists():
            raise ValidationError("This email address is already in use.")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

