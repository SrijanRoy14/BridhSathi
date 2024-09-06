from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from .models import *


class CustomUserForm(UserCreationForm):
    usable_password = None

    class Meta:
        model = User
        fields = ["username", "password1", "password2"]


class emergencyform(forms.ModelForm):
    class Meta:
        model = EmergencyContact
        fields = ["name", "phone_no"]

    def __init__(self, *args, **kwargs):
        super(emergencyform, self).__init__(*args, **kwargs)

    def save(self, commit=True, user=None):
        contact = super(emergencyform, self).save(commit=False)
        if user:  # Set the current logged-in user
            contact.user = user
        if commit:
            contact.save()
        return contact
