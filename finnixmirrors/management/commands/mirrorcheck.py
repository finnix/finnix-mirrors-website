import dateutil.parser
from django.core.management.base import BaseCommand
from django.utils import timezone
import requests

from finnixmirrors.models import MirrorURL


class Command(BaseCommand):
    help = "Mirror check"
    user_agent = (
        "Mozilla/5.0 (compatible; Finnix mirror checker; +http://mirrors.finnix.org/)"
    )
    trace_file = "project/trace/feh.colobox.com"
    head_file = "109/finnix-109.iso"
    head_expected_length = 137363456

    def request_url(self, url, method="GET"):
        headers = {"user-agent": self.user_agent}
        r = requests.request(method, url, headers=headers, timeout=5)
        r.raise_for_status()
        return r

    def check_mirrorurl(self, mirrorurl):
        now = timezone.now()
        mirrorurl.date_last_check = now
        try:
            r = self.request_url("{}/{}".format(mirrorurl.url, self.trace_file))
        except requests.exceptions.RequestException as e:
            mirrorurl.check_success = False
            mirrorurl.check_detail = str(e)
            mirrorurl.save()
            return

        try:
            mirrorurl.date_last_trace = dateutil.parser.parse(r.text.strip())
        except ValueError as e:
            mirrorurl.check_success = False
            mirrorurl.check_detail = str(e)
            mirrorurl.save()
            return

        try:
            r = self.request_url(
                "{}/{}".format(mirrorurl.url, self.head_file), method="HEAD"
            )
        except requests.exceptions.RequestException as e:
            mirrorurl.check_success = False
            mirrorurl.check_detail = str(e)
            mirrorurl.save()
            return

        head_got_length = int(r.headers["content-length"])
        if head_got_length != self.head_expected_length:
            mirrorurl.check_success = False
            mirrorurl.check_detail = "{} HEAD: Expected {}, got {}".format(
                self.head_file, self.head_expected_length, head_got_length
            )
            mirrorurl.save()
            return

        mirrorurl.check_success = True
        mirrorurl.date_last_success = now
        mirrorurl.check_detail = "Check OK"
        mirrorurl.save()

    def handle(self, *args, **options):
        for mirrorurl in MirrorURL.objects.filter(
            enabled=True, mirror__enabled=True, protocol__in=["http", "https"]
        ):
            self.check_mirrorurl(mirrorurl)
