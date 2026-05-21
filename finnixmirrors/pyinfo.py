# SPDX-FileCopyrightText: © 2019 Amos Vryhof
# SPDX-FileCopyrightText: © 2026 Ryan Finnie <ryan@finnie.org>
# SPDX-License-Identifier: MIT

# Based on https://github.com/avryhof/django_pyinfo

import os
import platform
import sys

from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_protect
from django.views.generic import TemplateView
from pip._internal.operations.freeze import freeze


class PyInfoView(TemplateView):
    """
    Show a page similar to phpinfo() about our virtual environment.
    """

    template_name = "pyinfo.html"

    def get_context_data(self, **kwargs):
        context = super(PyInfoView, self).get_context_data(**kwargs)
        context["page_title"] = "PyInfo"
        context["extra_css"] = []
        context["extra_javascript"] = []

        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()

        request_class = type(request).__name__.replace("Request", "")
        request_class_version_string = "%s.version" % request_class.lower()
        request_class_version = request.environ.get(request_class_version_string)

        context.update(
            {
                "copyright": mark_safe("<p>%s</p>" % sys.copyright.replace("\n\n", "</p><p>").replace("\n", "<br/>")),
                "os_version": platform.platform(),
                "os_platform": "{} {} {} {} {} {}".format(
                    platform.system(),
                    platform.node(),
                    platform.release(),
                    platform.version(),
                    platform.machine(),
                    platform.processor(),
                ),
                "api_version": sys.api_version,
                "build_date": platform.python_build()[1],
                "python_version": sys.version,
                "python_interpreter": sys.executable,
                "python_path": sys.path,
                "import_path": sys.path_importer_cache,
                "server_api": "%s %s" % (request_class, request_class_version),
                "packages": [],
                "request": request,
                "os_environment": os.environ,
            }
        )

        for package in freeze():
            package_parts = package.split("==", 1)
            package_name = package_parts[0]
            package_version = package_parts[1] if len(package_parts) > 1 else ""
            context["packages"].append({"name": package_name, "version": package_version})

        return render(request, self.template_name, context)

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super(PyInfoView, self).dispatch(*args, **kwargs)
