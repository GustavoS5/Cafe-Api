from urllib.parse import parse_qs, urlsplit

import pytest
from django.urls import reverse

from cafe.models import Cafe


pytestmark = pytest.mark.django_db


@pytest.fixture
def cafes(db, cafe_payload):
    return [
        Cafe.objects.create(**{**cafe_payload, "name": f"Cafe {25 - index}"})
        for index in range(25)
    ]


@pytest.mark.parametrize("route,params", [("all-cafes", {}), ("search-cafe", {"loc": "Cordoba"})])
def test_pagination_navigation(api_client, cafes, cafe_payload, route, params):
    if route == "search-cafe":
        Cafe.objects.create(**{**cafe_payload, "name": "Other", "location": "London"})

    response = api_client.get(reverse(route), params)
    seen = []
    for index, size in enumerate([10, 10, 5]):
        assert response.status_code == 200
        assert response.data["count"] == 25
        assert len(response.data["results"]) == size
        assert (response.data["previous"] is None) == (index == 0)
        seen.extend(item["id"] for item in response.data["results"])
        next_link = response.data["next"]
        if index == 2:
            assert next_link is None
        else:
            assert parse_qs(urlsplit(next_link).query)["page"] == [str(index + 2)]
            if route == "search-cafe":
                assert parse_qs(urlsplit(next_link).query)["loc"] == ["Cordoba"]
            response = api_client.get(next_link)

    assert seen == [cafe.pk for cafe in cafes]
    previous = api_client.get(response.data["previous"])
    assert previous.status_code == 200
    assert [item["id"] for item in previous.data["results"]] == seen[10:20]


@pytest.mark.parametrize("route,params", [("all-cafes", {}), ("search-cafe", {"loc": "Cordoba"})])
@pytest.mark.parametrize("page", [None, "1"])
def test_empty_collection(api_client, route, params, page):
    query = {**params}
    if page is not None:
        query["page"] = page
    response = api_client.get(reverse(route), query)

    assert response.status_code == 200
    assert response.data == {"count": 0, "next": None, "previous": None, "results": []}


@pytest.mark.parametrize("route,params", [("all-cafes", {}), ("search-cafe", {"loc": "Cordoba"})])
@pytest.mark.parametrize("page", ["0", "-1", "invalid", "1.5", "4"])
def test_invalid_page(api_client, cafes, route, params, page):
    response = api_client.get(reverse(route), {**params, "page": page})

    assert response.status_code == 404
    assert "detail" in response.data
