import hashlib
import logging

import dateutil.parser
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
import requests

from finnixmirrors.models import MirrorURL


class Command(BaseCommand):
    help = "Mirror check"
    user_agent = (
        "Mozilla/5.0 (compatible; Finnix mirror checker; +https://mirrors.finnix.org/)"
    )

    def request_url(self, url, method="GET", headers=None):
        full_headers = {"user-agent": self.user_agent}
        if headers is not None:
            full_headers.update(headers)
        r = requests.request(method, url, headers=full_headers, timeout=5)
        r.raise_for_status()
        return r

    def check_mirrorurl(self, mirrorurl):
        def mirrorurl_failure(mirrorurl, error):
            logging.debug("{} error: {}".format(mirrorurl, error))
            mirrorurl.check_success = False
            mirrorurl.check_detail = error
            mirrorurl.save()
            return

        now = timezone.now()
        mirrorurl.date_last_check = now
        if settings.CHECK_TRACE_FILE:
            try:
                r = self.request_url(
                    "{}/{}".format(mirrorurl.url, settings.CHECK_TRACE_FILE)
                )
            except requests.exceptions.RequestException as e:
                return mirrorurl_failure(mirrorurl, str(e))

            try:
                mirrorurl.date_last_trace = dateutil.parser.parse(r.text.strip())
            except ValueError as e:
                return mirrorurl_failure(mirrorurl, str(e))

        for data_file in settings.CHECK_DATA_FILES:
            if mirrorurl.head_allowed:
                try:
                    r = self.request_url(
                        "{}/{}".format(mirrorurl.url, data_file["path"]), method="HEAD"
                    )
                except requests.exceptions.RequestException as e:
                    return mirrorurl_failure(mirrorurl, str(e))

                head_got_length = int(r.headers["content-length"])
                if head_got_length != data_file["length"]:
                    return mirrorurl_failure(
                        mirrorurl,
                        "{} HEAD: Expected {}, got {}".format(
                            data_file["path"], data_file["length"], head_got_length
                        ),
                    )

            if mirrorurl.range_allowed:
                for range in data_file.get("ranges", []):
                    try:
                        r = self.request_url(
                            "{}/{}".format(mirrorurl.url, data_file["path"]),
                            headers={
                                "Range": "bytes={}-{}".format(
                                    range["begin"], range["end"]
                                )
                            },
                        )
                    except requests.exceptions.RequestException as e:
                        return mirrorurl_failure(mirrorurl, str(e))

                    sha256sum_got = hashlib.sha256(r.content).hexdigest()
                    if sha256sum_got != range["sha256sum"]:
                        return mirrorurl_failure(
                            mirrorurl,
                            "{} range {}-{}: Expected {}, got {}".format(
                                data_file["path"],
                                range["begin"],
                                range["end"],
                                range["sha256sum"],
                                sha256sum_got,
                            ),
                        )

        mirrorurl.check_success = True
        mirrorurl.date_last_success = now
        mirrorurl.check_detail = "Check OK"
        mirrorurl.save()

    def handle(self, *args, **options):
        logging.getLogger("").setLevel(
            logging.DEBUG if int(options["verbosity"]) >= 2 else logging.INFO
        )

        for mirrorurl in MirrorURL.objects.filter(
            enabled=True, mirror__enabled=True, protocol__in=["http", "https"]
        ):
            logging.debug("Checking {}".format(mirrorurl))
            self.check_mirrorurl(mirrorurl)
