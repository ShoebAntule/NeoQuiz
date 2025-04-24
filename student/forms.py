from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from . import models
from quiz import models as QMODEL
import re

class StudentUserForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput()
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@eng.rizvi.edu.in'):
            raise ValidationError("Email must end with @eng.rizvi.edu.in")
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists")
        return email

class StudentForm(forms.ModelForm):
    class Meta:
        model = models.Student
        fields = ['address', 'mobile', 'profile_pic']

class StudentLoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email", max_length=254)

    def clean_username(self):
        email = self.cleaned_data.get('username')
        if not email.endswith('@eng.rizvi.edu.in'):
            raise ValidationError("Email must end with @eng.rizvi.edu.in")
        return email
