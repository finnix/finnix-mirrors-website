from django.contrib import admin

from .models import MirrorURL, Mirror


class MirrorAdmin(admin.ModelAdmin):
    list_display = ("slug", "enabled", "country", "sponsor")
    ordering = ("slug",)
    search_fields = ("slug", "sponsor", "location")
    list_filter = ("enabled",)


class MirrorURLAdmin(admin.ModelAdmin):
    list_display = (
        "protocol",
        "mirror",
        "enabled",
        "weight",
        "check_success",
        "date_last_check",
        "date_last_success",
        "date_last_trace",
    )
    ordering = ("mirror", "protocol")
    search_fields = ("mirror__slug", "mirror__sponsor", "url")
    list_filter = ("enabled", "check_success")


admin.site.register(Mirror, MirrorAdmin)
admin.site.register(MirrorURL, MirrorURLAdmin)
