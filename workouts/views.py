from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard_view(request):
    """
    Main member dashboard: displays today's scheduled workout,
    plant-based nutrition tracker, and recovery status.
    Protected by authentication.
    """
    return render(request, "dashboard.html")
