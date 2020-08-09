from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("mirror/<slug>/", views.MirrorView.as_view(), name="mirror"),
    path("releases/", views.releases, name="releases"),
    path("releases/<path:path>", views.releases, name="releases"),
    path("", views.index, name="index"),
]
