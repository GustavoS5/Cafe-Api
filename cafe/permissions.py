from django.conf import settings
from django.utils.crypto import constant_time_compare
from rest_framework.permissions import BasePermission, SAFE_METHODS


class ReadOnlyOrHasAPIKey(BasePermission):
    message = "Invalid or missing API key."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        supplied_key = request.headers.get("X-API-KEY", "")
        return bool(settings.API_KEY) and constant_time_compare(
            supplied_key, settings.API_KEY
        )
