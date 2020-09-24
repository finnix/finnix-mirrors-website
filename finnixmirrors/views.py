from datetime import timedelta
import ipaddress
import random

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.utils import timezone
from django.views import generic

try:
    import geoip2.database as geoip_db
except ImportError as e:
    geoip_db = e

try:
    from geopy.distance import geodesic
except ImportError as e:
    geodesic = e

from .models import Mirror, MirrorURL


class MirrorView(generic.DetailView):
    template_name = "finnixmirrors/mirror.html"
    model = Mirror


def index(request):
    now = timezone.now()
    outdated_time = now - timedelta(hours=28)

    mirrors = []
    for mirror in Mirror.objects.filter(enabled=True).order_by("country", "slug"):
        status = "good"
        mirrorurls = mirror.mirrorurl_set.filter(enabled=True)
        for mirrorurl in mirrorurls:
            setattr(mirrorurl, "outdated", False)
            if mirrorurl.date_last_trace and mirrorurl.date_last_trace < outdated_time:
                setattr(mirrorurl, "outdated", True)
                status = "outdated"
        for mirrorurl in mirrorurls:
            if not mirrorurl.check_success:
                status = "error"
                break
        setattr(
            mirror,
            "urls_last_trace",
            max([x.date_last_trace for x in mirrorurls if x.date_last_trace]),
        )
        setattr(mirror, "mirrorurls", mirrorurls)
        setattr(mirror, "status", status)
        mirrors.append(mirror)

    context = {"mirrors": mirrors}
    template = loader.get_template("finnixmirrors/index.html")
    return HttpResponse(template.render(context, request))


def get_geoip_mirror(mirrorurls, ip):
    if not hasattr(settings, "GEOIP2_DB") or not settings.GEOIP2_DB:
        return
    if isinstance(geoip_db, ImportError):
        return
    if isinstance(geodesic, ImportError):
        return

    try:
        with geoip_db.Reader(settings.GEOIP2_DB) as reader:
            response = reader.city(ip)
        ip_location = (response.location.latitude, response.location.longitude)
    except Exception:
        return

    distances = {}
    for mirrorurl in mirrorurls:
        if (not mirrorurl.mirror.latitude) or (not mirrorurl.mirror.longitude):
            continue
        mirror_location = (mirrorurl.mirror.latitude, mirrorurl.mirror.longitude)
        mirror_distance = geodesic(ip_location, mirror_location).kilometers
        weighted_distance = mirror_distance / mirrorurl.weight
        distances[weighted_distance] = (mirrorurl, mirror_distance)

    if not distances:
        return
    weighted_distance = sorted(distances.keys())[0]
    return distances[weighted_distance]


def releases(request, path=""):
    now = timezone.now()
    outdated_time = now - timedelta(hours=28)
    ip = ipaddress.ip_address(request.META["REMOTE_ADDR"])

    mirrorurls = MirrorURL.objects.filter(
        enabled=True,
        protocol="https",
        check_success=True,
        date_last_trace__isnull=False,
        date_last_trace__gte=outdated_time,
        mirror__enabled=True,
    )

    geoip_mirror = get_geoip_mirror(mirrorurls, ip)

    if geoip_mirror:
        mirrorurl = geoip_mirror[0]
    else:
        mirrorurl = random.choice(mirrorurls)
    url = "{}/{}".format(mirrorurl.url, path)

    response = HttpResponseRedirect(url)
    response["X-GeoIP-Ip"] = str(ip)
    if mirrorurl.mirror.sponsor:
        response["X-Mirror-Sponsor"] = mirrorurl.mirror.sponsor
    if mirrorurl.mirror.sponsor_url:
        response["X-Mirror-Sponsor-Url"] = mirrorurl.mirror.sponsor_url
    if geoip_mirror:
        response["X-GeoIP-Influenced"] = "yes"
        response["X-Mirror-Distance-Km"] = str(int(geoip_mirror[1]))
    else:
        response["X-GeoIP-Influenced"] = "no"
    return response
