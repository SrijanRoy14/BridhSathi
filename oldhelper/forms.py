from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User


class CustomUserForm(UserCreationForm):
    usable_password = None

    class Meta:
        model = User
        fields = ["username", "password1", "password2"]
