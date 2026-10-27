import pytest
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from cafe.permissions import ReadOnlyOrHasAPIKey


@pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS"])
def test_safe_methods_do_not_require_api_key(settings, method):
    settings.API_KEY = "test-api-key"
    request = APIRequestFactory().generic(method, "/")

    assert ReadOnlyOrHasAPIKey().has_permission(request, None)


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
@pytest.mark.parametrize("key,allowed", [("", False), ("incorrect", False), ("test-api-key", True)])
def test_unsafe_methods_require_valid_api_key(settings, method, key, allowed):
    settings.API_KEY = "test-api-key"
    request = APIRequestFactory().generic(method, "/", HTTP_X_API_KEY=key)

    assert ReadOnlyOrHasAPIKey().has_permission(request, None) is allowed


def test_empty_configured_key_never_allows_writes(settings):
    settings.API_KEY = ""
    request = APIRequestFactory().post("/")

    assert not ReadOnlyOrHasAPIKey().has_permission(request, None)


def test_new_view_inherits_global_permission(settings):
    settings.API_KEY = "test-api-key"
    calls = []

    @api_view(["POST"])
    def write_view(request):
        calls.append(True)
        return Response({"ok": True})

    factory = APIRequestFactory()
    response = write_view(factory.post("/"))

    assert response.status_code == 403
    assert "detail" in response.data
    assert calls == []

    response = write_view(factory.post("/", HTTP_X_API_KEY="test-api-key"))

    assert response.status_code == 200
    assert calls == [True]
