from django import forms
from django.contrib.auth.forms import AuthenticationForm


class GymAuthenticationForm(AuthenticationForm):
    """
    High-contrast, mobile-friendly authentication form.
    Touch targets meet the minimum 48px standard for gym usability.
    """

    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(
            attrs={
                "class": "input-gym",
                "placeholder": "Enter your username",
                "autocomplete": "username",
                "autocapitalize": "none",
                "autocorrect": "off",
                "spellcheck": "false",
                "id": "id_username",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "input-gym pr-12",
                "placeholder": "Enter your password",
                "autocomplete": "current-password",
                "id": "id_password",
            }
        ),
    )
