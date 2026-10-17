from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.views import View

from accounts.forms import GymAuthenticationForm


class UserLoginView(LoginView):
    """
    Custom login view using the high-contrast gym theme
    and touch-friendly input styling.
    """

    form_class = GymAuthenticationForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class UserLogoutView(View):
    """
    Clean logout handler supporting both POST and GET requests,
    redirecting to the home page.
    """

    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect("/")

    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect("/")
