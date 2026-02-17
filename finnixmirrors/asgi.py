# SPDX-PackageName: finnix-mirrors-website
# SPDX-PackageSupplier: Ryan Finnie <ryan@finnie.org>
# SPDX-PackageDownloadLocation: https://github.com/finnix/finnix-mirrors-website
# SPDX-FileCopyrightText: © 2020 Ryan Finnie <ryan@finnie.org>
# SPDX-License-Identifier: MPL-2.0

"""
ASGI config for finnixmirrors project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finnixmirrors.settings")

application = get_asgi_application()
