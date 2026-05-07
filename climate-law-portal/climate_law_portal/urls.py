"""Project-level URL configuration."""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from core.views import about_view, health_view


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("cases.urls", "cases"), namespace="cases")),
    path("about/", about_view, name="about"),
    path("health/", health_view, name="health"),
    path("favicon.ico", RedirectView.as_view(url="/static/favicon.ico", permanent=True)),
]

handler404 = "core.views.handler404"
handler500 = "core.views.handler500"

admin.site.site_header = "Climate Law Intelligence Portal — Admin"
admin.site.site_title = "Climate Law Portal"
admin.site.index_title = "Case Database Administration"
