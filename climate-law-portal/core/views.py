"""Core views: about page, health probe, custom error handlers."""
from django.http import HttpResponse
from django.shortcuts import render


def about_view(request):
    return render(request, "core/about.html")


def health_view(request):
    """Plain-text health endpoint suitable for Render's health check."""
    return HttpResponse("ok", content_type="text/plain")


def handler404(request, exception=None):
    return render(request, "core/404.html", status=404)


def handler500(request):
    return render(request, "core/500.html", status=500)
