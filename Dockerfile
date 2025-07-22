# SPDX-PackageSummary: finnix-mirrors-website
# SPDX-FileCopyrightText: Copyright (C) 2020-2025 Ryan Finnie
# SPDX-License-Identifier: MPL-2.0
FROM python:3.12

WORKDIR /usr/src/app

COPY . .
RUN pip install --no-cache-dir gunicorn .

RUN apt-get update && apt-get -y install rsync && apt-get clean

USER nobody
ENV DJANGO_SETTINGS_MODULE="finnixmirrors.settings"
ENV PYTHONPATH=/usr/local/lib/python
CMD [ "gunicorn", "-b", "0.0.0.0:8000", "-k", "gthread", "--error-logfile", "-", "--capture-output", "finnixmirrors.wsgi:application" ]
EXPOSE 8000/tcp
