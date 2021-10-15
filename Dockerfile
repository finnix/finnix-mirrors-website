FROM ubuntu:20.04

ENV DJANGO_MODULE=finnixmirrors

COPY . /tmp/django
RUN /tmp/django/docker/build && rm -rf /tmp/django

EXPOSE 8000/tcp

USER nobody
CMD ["/init"]
