# SPDX-PackageName: finnix-mirrors-website
# SPDX-PackageSupplier: Ryan Finnie <ryan@finnie.org>
# SPDX-PackageDownloadLocation: https://forge.colobox.com/finnix/finnix-mirrors-website
# SPDX-FileCopyrightText: © 2020 Ryan Finnie <ryan@finnie.org>
# SPDX-License-Identifier: MPL-2.0

from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("mirror/<slug>/", views.MirrorView.as_view(), name="mirror"),
    path("mirrors.json", views.mirrors_json, name="mirrors_json"),
    path("releases/", views.releases, name="releases"),
    path("releases/<path:path>", views.releases, name="releases"),
    path("", views.index, name="index"),
]
