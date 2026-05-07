"""URL routes for the cases app."""
from django.urls import path

from . import views


app_name = "cases"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("search/", views.search_view, name="search"),
    path("case/<int:pk>/", views.case_detail_by_pk_only, name="detail_short"),
    path("case/<int:pk>/<slug:slug>/", views.case_detail_view, name="detail"),
]
