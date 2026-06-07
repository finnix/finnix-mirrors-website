# SPDX-PackageName: finnix-mirrors-website
# SPDX-PackageSupplier: Ryan Finnie <ryan@finnie.org>
# SPDX-PackageDownloadLocation: https://forge.colobox.com/finnix/finnix-mirrors-website
# SPDX-FileCopyrightText: © 2020 Ryan Finnie <ryan@finnie.org>
# SPDX-License-Identifier: MPL-2.0
FROM python:3.14-slim

COPY . /tmp/build
RUN pip install --no-cache-dir '/tmp/build[gunicorn]' && useradd -ms /bin/bash app && rm -rf /tmp/build
RUN apt-get update && apt-get -y install rsync && apt-get clean

ENV DJANGO_SETTINGS_MODULE="finnixmirrors.settings"
USER app
CMD [ "gunicorn", "-b", "0.0.0.0:8000", "-k", "gthread", "--error-logfile", "-", "--capture-output", "finnixmirrors.wsgi:application" ]
EXPOSE 8000/tcp
