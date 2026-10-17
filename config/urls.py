"""
URL configuration for GROW project.

The `urlpatterns` list routes URLs to views.
https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""

from django.contrib import admin
from django.shortcuts import redirect, render
from django.urls import include, path

from workouts.views import dashboard_view


def home_view(request):
    """
    Landing / welcome view for GROW.
    If authenticated, redirects to the member dashboard.
    If unauthenticated, displays the welcome page.
    """
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "index.html")


urlpatterns = [
    path("", home_view, name="home"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("accounts/", include("accounts.urls")),
    path("admin/", admin.site.urls),
    path("workouts/", include("workouts.urls")),
    path("nutrition/", include("nutrition.urls")),
]
