from django.core.management.base import BaseCommand

from finnixmirrors.views import get_geoip_mirrors, get_mirrorurls


def collapse_names(d, lang="en"):
    if isinstance(d, dict) and "names" in d:
        if lang in d["names"]:
            name = d["names"][lang]
        else:
            name = d["names"].items()[0][1]
        d["name"] = name
        del d["names"]
    if isinstance(d, dict):
        for k in d:
            collapse_names(d[k])
    elif isinstance(d, list):
        for k in d:
            collapse_names(k)


class Command(BaseCommand):
    help = "GeoIP mirror info"

    def add_arguments(self, parser):
        parser.add_argument("ip")

    def handle(self, *args, **options):
        ip = options["ip"]
        mirrorurls = get_mirrorurls()
        ret = get_geoip_mirrors(mirrorurls, ip)
        if not ret:
            print("No GeoIP information for {}".format(ip))
            return
        distances, geoip_response = ret

        print("IP: {}".format(ip))
        print(
            "GeoIP (https://www.openstreetmap.org/?mlat={}&mlon={}):".format(
                geoip_response.location.latitude, geoip_response.location.longitude
            )
        )
        geo = geoip_response.raw
        collapse_names(geo)
        for k, v in geo.items():
            print("    {} = {}".format(k, v))
        print("Mirrors:")
        for mirrorurl_info in sorted(distances, key=lambda x: x[2]):
            mirrorurl = mirrorurl_info[0]
            distance = mirrorurl_info[1]
            weighted_distance = mirrorurl_info[2]
            print(
                "    distance = {:6.0f}, weighted distance = {:6.0f} (weight {:5.02f}): {}".format(
                    distance, weighted_distance, mirrorurl.weight, mirrorurl
                )
            )
