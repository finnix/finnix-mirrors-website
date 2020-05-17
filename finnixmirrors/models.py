import uuid

from django.db import models
from django.urls import reverse_lazy


class Mirror(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, blank=False, null=False
    )
    slug = models.SlugField(unique=True, blank=False, null=False)
    enabled = models.BooleanField(default=True)
    country = models.CharField(max_length=2, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    map_zoom = models.IntegerField(blank=True, null=True)
    sponsor = models.CharField(max_length=200, blank=True, null=True)
    sponsor_url = models.CharField(max_length=4095, blank=True, null=True)

    def get_absolute_url(self):
        return reverse_lazy("mirror", kwargs={"slug": self.slug})

    def __str__(self):
        return self.slug


class MirrorURL(models.Model):
    PROTOCOLS = (
        ("http", "HTTP"),
        ("https", "HTTPS"),
        ("ftp", "FTP"),
        ("rsync", "Rsync"),
    )

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, blank=False, null=False
    )
    mirror = models.ForeignKey(
        Mirror, on_delete=models.CASCADE, blank=False, null=False
    )
    url = models.CharField(max_length=4095, blank=True, null=True)
    protocol = models.CharField(
        max_length=200, choices=PROTOCOLS, blank=False, null=False
    )
    ipv4 = models.BooleanField(default=True)
    ipv6 = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)
    weight = models.FloatField(default=1.0, blank=False, null=False)
    check_success = models.BooleanField(default=True)
    check_detail = models.TextField(blank=True, null=True)
    date_last_check = models.DateTimeField(blank=True, null=True)
    date_last_success = models.DateTimeField(blank=True, null=True)
    date_last_trace = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "{} {}".format(self.mirror.slug, self.protocol)
