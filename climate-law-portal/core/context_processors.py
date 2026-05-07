"""Inject site-wide template variables."""
from django.conf import settings


def site_meta(request):
    return {
        "SITE_NAME": "Climate Law Intelligence Portal — Pakistan",
        "SITE_TAGLINE": "Search and analyze 5,000+ Pakistan climate & environmental cases.",
        "DEBUG": settings.DEBUG,
    }
