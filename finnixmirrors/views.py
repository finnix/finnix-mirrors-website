import ipaddress
import random

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.views.generic.detail import DetailView

try:
    import geoip2.database as geoip_db
except ImportError as e:
    geoip_db = e

try:
    from geopy.distance import distance
except ImportError as e:
    distance = e

from .models import Mirror, MirrorURL


class MirrorView(DetailView):
    template_name = "finnixmirrors/mirror.html"
    model = Mirror

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        _mirror_populate(context["mirror"])
        return context


def _mirror_populate(mirror):
    status = "good"
    mirrorurls = mirror.mirrorurl_set.filter(enabled=True)
    for mirrorurl in mirrorurls:
        if mirrorurl.outdated:
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


def _mirror_info():
    mirrors = []
    for mirror in Mirror.objects.filter(enabled=True).order_by("country", "slug"):
        _mirror_populate(mirror)
        mirrors.append(mirror)
    return mirrors


def mirrors_json(request):
    out = {}
    for mirror in _mirror_info():
        m = {
            "country": mirror.country,
            "location": mirror.location,
            "sponsor": mirror.sponsor,
            "sponsor_url": mirror.sponsor_url,
            "latitude": mirror.latitude,
            "longitude": mirror.longitude,
            "urls": [],
        }
        for mirrorurl in mirror.mirrorurls:
            m["urls"].append(
                {
                    "url": mirrorurl.url,
                    "protocol": mirrorurl.protocol,
                    "ipv4": mirrorurl.ipv4,
                    "ipv6": mirrorurl.ipv6,
                    "check_success": mirrorurl.check_success,
                    "date_last_check": mirrorurl.date_last_check,
                    "date_last_success": mirrorurl.date_last_success,
                    "date_last_trace": mirrorurl.date_last_trace,
                    "head_allowed": mirrorurl.head_allowed,
                    "range_allowed": mirrorurl.range_allowed,
                }
            )
        out[mirror.slug] = m

    return JsonResponse({"mirrors": out})


def index(request):
    context = {"mirrors": _mirror_info()}
    template = loader.get_template("finnixmirrors/index.html")
    return HttpResponse(template.render(context, request))


def get_geoip_mirrors(mirrorurls, ip):
    if not hasattr(settings, "GEOIP2_DB") or not settings.GEOIP2_DB:
        return
    if isinstance(geoip_db, ImportError):
        return
    if isinstance(distance, ImportError):
        return

    try:
        with geoip_db.Reader(settings.GEOIP2_DB) as reader:
            geoip_response = reader.city(ip)
        ip_location = (
            geoip_response.location.latitude,
            geoip_response.location.longitude,
        )
    except Exception:
        return

    distances = []
    for mirrorurl in mirrorurls:
        if (not mirrorurl.mirror.latitude) or (not mirrorurl.mirror.longitude):
            continue
        mirror_location = (mirrorurl.mirror.latitude, mirrorurl.mirror.longitude)
        mirror_distance = distance(ip_location, mirror_location).kilometers
        weighted_distance = mirror_distance / mirrorurl.weight
        distances.append((mirrorurl, mirror_distance, weighted_distance))

    return (distances, geoip_response)


def get_geoip_mirror(mirrorurls, ip):
    ret = get_geoip_mirrors(mirrorurls, ip)
    if not ret:
        return
    distances, geoip_response = ret
    return sorted(distances, key=lambda x: x[2])[0]


def get_mirrorurls():
    mirrorurls = MirrorURL.objects.filter(
        enabled=True,
        protocol="https",
        check_success=True,
        mirror__enabled=True,
    )

    fresh_mirrorurls = [x for x in mirrorurls if not x.outdated]
    return fresh_mirrorurls if fresh_mirrorurls else mirrorurls


def releases(request, path=""):
    ip = ipaddress.ip_address(request.META["REMOTE_ADDR"])

    mirrorurls = get_mirrorurls()
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
