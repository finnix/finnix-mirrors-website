from datetime import timedelta

from django.http import HttpResponse
from django.template import loader
from django.utils import timezone
from django.views import generic

from .models import Mirror


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
