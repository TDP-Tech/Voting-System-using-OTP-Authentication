
# election/admin.py
from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Student, Vote, Candidate,Category

class StudentAdminCreationForm(forms.ModelForm):
    email = forms.EmailField(label='Email', required=True)
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = Student
        fields = ('student_id', 'email', 'password1', 'password2', 'otp', 'is_active', 'is_admin')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Student.objects.filter(email=email).exists():
            raise forms.ValidationError('A student with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class StudentAdminChangeForm(forms.ModelForm):
    email = forms.EmailField(label='Email', required=True)
    password = forms.CharField(label='Password', widget=forms.PasswordInput, required=False, help_text="Leave empty if you don't want to change the password")

    class Meta:
        model = Student
        fields = ('student_id', 'email', 'password', 'otp', 'is_active', 'is_admin')

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if not password:
            return self.instance.password
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data["password"]:
            user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user



@admin.register(Student)
class StudentAdmin(UserAdmin):
    form = StudentAdminChangeForm
    add_form = StudentAdminCreationForm

    list_display = ('student_id', 'email', 'is_active', 'is_admin')
    list_filter = ('is_admin', 'is_active')
    fieldsets = (
        (None, {'fields': ('student_id', 'email', 'password')}),
        ('Personal info', {'fields': ('otp',)}),
        ('Permissions', {'fields': ('is_admin', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('student_id', 'email', 'password1', 'password2', 'otp', 'is_active', 'is_admin')}
        ),
    )
    search_fields = ('student_id', 'email')
    ordering = ('student_id',)
    filter_horizontal = ()


class VoteAdmin(admin.ModelAdmin):
    list_display = ('student', 'candidate', 'timestamp')
    search_fields = ('student__student_id', 'candidate')
    list_filter = ('candidate', 'timestamp')
admin.site.register(Vote, VoteAdmin)

class CandidateAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'middle_name', 'last_name', 'course', 'level_of_study', 'year_of_study', 'position', 'category')
    list_filter = ('course', 'level_of_study', 'year_of_study', 'position')

admin.site.register(Candidate, CandidateAdmin)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['category_name']
