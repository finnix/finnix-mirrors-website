import ftplib
import hashlib
import logging
import random
import subprocess
import tempfile
import urllib.parse

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

    def __init__(self):
        self.rs = requests.Session()
        self.rs.headers.update({"user-agent": self.user_agent})

    def safe_sample(self, population, k):
        if k > len(population):
            return population
        elif k < 1:
            return []
        return random.sample(population, int(k))

    def request_url(self, url, method="GET", headers=None):
        r = self.rs.request(method, url, headers=headers, timeout=5)
        r.raise_for_status()
        return r

    def mirrorurl_failure(self, mirrorurl, error):
        logging.debug("{} error: {}".format(mirrorurl, error))
        mirrorurl.check_success = False
        mirrorurl.check_detail = error
        mirrorurl.save()

    def check_mirrorurl(self, mirrorurl):
        if mirrorurl.protocol in ("http", "https"):
            return self.check_mirrorurl_http(mirrorurl)
        elif mirrorurl.protocol == "rsync":
            return self.check_mirrorurl_rsync(mirrorurl)
        elif mirrorurl.protocol == "ftp":
            return self.check_mirrorurl_ftp(mirrorurl)

    def check_mirrorurl_http(self, mirrorurl):
        now = timezone.now()
        mirrorurl.date_last_check = now
        if settings.CHECK_TRACE_FILE:
            r = self.request_url(
                "{}/{}".format(mirrorurl.url, settings.CHECK_TRACE_FILE)
            )
            mirrorurl.date_last_trace = dateutil.parser.parse(r.text.strip())

        for data_file in self.safe_sample(
            settings.CHECK_DATA_FILES, settings.CHECK_DATA_FILE_COUNT
        ):
            if mirrorurl.head_allowed:
                r = self.request_url(
                    "{}/{}".format(mirrorurl.url, data_file["path"]), method="HEAD"
                )

                head_got_length = int(r.headers["content-length"])
                if head_got_length != data_file["length"]:
                    return self.mirrorurl_failure(
                        mirrorurl,
                        "{} HEAD: Expected {}, got {}".format(
                            data_file["path"], data_file["length"], head_got_length
                        ),
                    )

            if mirrorurl.range_allowed:
                for range in self.safe_sample(
                    data_file.get("ranges", []), settings.CHECK_DATA_FILE_RANGE_COUNT
                ):
                    r = self.request_url(
                        "{}/{}".format(mirrorurl.url, data_file["path"]),
                        headers={
                            "Range": "bytes={}-{}".format(range["begin"], range["end"])
                        },
                    )

                    hash_got = hashlib.new(
                        range.get("hash_type", "sha256"), r.content
                    ).hexdigest()
                    if hash_got != range["hash"]:
                        return self.mirrorurl_failure(
                            mirrorurl,
                            "{} range {}-{}: Expected {}, got {}".format(
                                data_file["path"],
                                range["begin"],
                                range["end"],
                                range["hash"],
                                hash_got,
                            ),
                        )

        mirrorurl.check_success = True
        mirrorurl.date_last_success = now
        mirrorurl.check_detail = "Check OK"
        mirrorurl.save()

    def check_mirrorurl_rsync(self, mirrorurl):
        now = timezone.now()
        mirrorurl.date_last_check = now
        if not settings.CHECK_TRACE_FILE:
            return
        tmp = tempfile.NamedTemporaryFile(mode="w+", encoding="UTF-8")
        res = subprocess.check_output(
            [
                "rsync",
                "-v",
                "--timeout=10",
                "--contimeout=10",
                "{}/{}".format(mirrorurl.url, settings.CHECK_TRACE_FILE),
                tmp.name,
            ],
            encoding="UTF-8",
            stderr=subprocess.STDOUT,
        )

        # In theory, tmp.read() should just work and we wouldn't need to re-open.
        # In practice, it always returns an empty string in the Django environment,
        # and I've never been able to figure out why.
        with open(tmp.name) as f:
            date_last_trace_text = f.read().strip()
        mirrorurl.date_last_trace = dateutil.parser.parse(date_last_trace_text)

        mirrorurl.check_success = True
        mirrorurl.date_last_success = now
        mirrorurl.check_detail = res
        mirrorurl.save()

    def check_mirrorurl_ftp(self, mirrorurl):
        now = timezone.now()
        mirrorurl.date_last_check = now
        if not settings.CHECK_TRACE_FILE:
            return

        self._line = ""

        def _cb(self, line):
            if not self._line:
                self._line = line

        url = urllib.parse.urlsplit(
            "{}/{}".format(mirrorurl.url, settings.CHECK_TRACE_FILE)
        )
        ftp = ftplib.FTP(url.netloc, timeout=5)
        ftp.login()
        ftp.retrlines(
            "RETR {}".format(url.path), callback=(lambda line: _cb(self, line))
        )
        ftp.quit()
        mirrorurl.date_last_trace = dateutil.parser.parse(self._line.strip())

        mirrorurl.check_success = True
        mirrorurl.date_last_success = now
        mirrorurl.check_detail = "Check OK"
        mirrorurl.save()

    def add_arguments(self, parser):
        parser.add_argument("--mirror", nargs="*")

    def handle(self, *args, **options):
        logging.getLogger("").setLevel(
            logging.DEBUG if int(options["verbosity"]) >= 2 else logging.INFO
        )

        opt_filter = {}
        if options["mirror"]:
            opt_filter["mirror__slug__in"] = options["mirror"]
        else:
            opt_filter["mirror__enabled"] = True

        for mirrorurl in MirrorURL.objects.filter(
            enabled=True,
            protocol__in=["http", "https", "rsync", "ftp"],
            **opt_filter,
        ):
            logging.debug("Checking {}".format(mirrorurl))
            try:
                self.check_mirrorurl(mirrorurl)
            except Exception as e:
                self.mirrorurl_failure(mirrorurl, str(e))
