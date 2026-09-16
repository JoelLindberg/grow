"""
URL configuration for GROW project.

The `urlpatterns` list routes URLs to views.
https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
    path("admin/", admin.site.urls),
    path("workouts/", include("workouts.urls")),
    path("nutrition/", include("nutrition.urls")),
]
