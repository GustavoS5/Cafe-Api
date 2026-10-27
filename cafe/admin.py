from django.contrib import admin
from cafe.models import Cafe


@admin.register(Cafe)
class CafeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "location",
        "seats",
        "has_wifi",
        "has_sockets",
        "can_take_calls",
        "coffee_price",
    )
    search_fields = ("name", "location")
    list_filter = (
        "has_wifi",
        "has_sockets",
        "has_toilet",
        "can_take_calls",
        "location",
    )
