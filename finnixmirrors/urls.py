from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("mirror/<slug>/", views.MirrorView.as_view(), name="mirror"),
    path("", views.index, name="index"),
]
