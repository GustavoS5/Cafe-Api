from decimal import Decimal

import pytest
from django.urls import reverse
from django.db import IntegrityError, transaction
from rest_framework import status

from cafe.models import Cafe


pytestmark = pytest.mark.django_db


def test_update_cafe_price_persists_change(authorized_client, cafe):
    response = authorized_client.patch(
        reverse("update-cafe-price", args=[cafe.pk]),
        {"coffee_price": "3.00"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    cafe.refresh_from_db()
    assert cafe.coffee_price == Decimal("3.00")


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({}, id="missing"),
        pytest.param({"coffee_price": ""}, id="blank"),
        pytest.param({"coffee_price": "   "}, id="whitespace"),
        pytest.param({"coffee_price": None}, id="null"),
        pytest.param({"coffee_price": "x" * 251}, id="too-long"),
        pytest.param({"coffee_price": []}, id="list"),
        pytest.param({"coffee_price": {}}, id="object"),
        pytest.param({"coffee_price": "-0.01"}, id="negative"),
        pytest.param({"coffee_price": "1.234"}, id="too-many-decimals"),
        pytest.param({"coffee_price": "100000000.00"}, id="out-of-range"),
        pytest.param({"coffee_price": "$3.00"}, id="currency-symbol"),
        pytest.param({"coffee_price": "NaN"}, id="nan"),
        pytest.param({"coffee_price": "Infinity"}, id="infinity"),
        pytest.param({"coffee_price": True}, id="boolean"),
    ],
)
def test_update_cafe_price_rejects_invalid_values(authorized_client, cafe, payload):
    response = authorized_client.patch(
        reverse("update-cafe-price", args=[cafe.pk]),
        payload,
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "coffee_price" in response.data
    cafe.refresh_from_db()
    assert cafe.coffee_price == Decimal("2.50")


def test_update_cafe_price_accepts_maximum_amount(authorized_client, cafe):
    price = "99999999.99"
    response = authorized_client.patch(
        reverse("update-cafe-price", args=[cafe.pk]),
        {"coffee_price": price},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    cafe.refresh_from_db()
    assert cafe.coffee_price == Decimal(price)


def test_update_cafe_price_ignores_other_fields(authorized_client, cafe):
    response = authorized_client.patch(
        reverse("update-cafe-price", args=[cafe.pk]),
        {"coffee_price": "3.00", "name": "Changed name"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    cafe.refresh_from_db()
    assert cafe.coffee_price == Decimal("3.00")
    assert cafe.name == "Test Cafe"


def test_update_cafe_price_requires_valid_api_key(api_client, cafe):
    response = api_client.patch(
        reverse("update-cafe-price", args=[cafe.pk]),
        {"coffee_price": "3.00"},
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "detail" in response.data
    cafe.refresh_from_db()
    assert cafe.coffee_price == Decimal("2.50")


def test_add_cafe_requires_valid_api_key(api_client):
    response = api_client.post(
        reverse("add-cafe"),
        {
            "name": "New Cafe",
            "map_url": "https://maps.example.com/new-cafe",
            "img_url": "https://images.example.com/new-cafe.jpg",
            "location": "Cordoba",
            "seats": "10-20",
            "has_toilet": True,
            "has_wifi": True,
            "has_sockets": False,
            "can_take_calls": False,
            "coffee_price": "2.00",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "detail" in response.data
    assert not Cafe.objects.filter(name="New Cafe").exists()


def test_delete_cafe_requires_valid_api_key(api_client, cafe):
    response = api_client.delete(reverse("delete-cafe", args=[cafe.pk]))

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "detail" in response.data
    assert Cafe.objects.filter(pk=cafe.pk).exists()


def test_get_all_cafes(api_client, cafe, cafe_payload):
    other = Cafe.objects.create(**cafe_payload)
    response = api_client.get(reverse("all-cafes"))

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.data["results"]] == [cafe.pk, other.pk]
    assert response.data["count"] == 2
    assert response.data["next"] is None
    assert response.data["previous"] is None


def test_get_random_cafe(api_client, cafe):
    response = api_client.get(reverse("random-cafe"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == cafe.pk
    assert response.data["name"] == cafe.name
    assert response.data["coffee_price"] == "2.50"
    assert response.data["currency"] == "USD"


def test_random_cafe_empty_database(api_client):
    response = api_client.get(reverse("random-cafe"))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data == {"error": "No cafes found."}


def test_search_matches_location_case_insensitively(api_client, cafe, cafe_payload):
    Cafe.objects.create(**cafe_payload)
    response = api_client.get(reverse("search-cafe"), {"loc": "bUeNoS"})

    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.data["results"]] == [cafe.pk]
    assert response.data["count"] == 1


@pytest.mark.parametrize("params", [{}, {"loc": ""}])
def test_search_requires_location(api_client, params):
    response = api_client.get(reverse("search-cafe"), params)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.data


def test_search_no_matches(api_client, cafe):
    response = api_client.get(reverse("search-cafe"), {"loc": "Unknown"})

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"count": 0, "next": None, "previous": None, "results": []}


def test_add_cafe_persists_all_fields(authorized_client, cafe_payload):
    response = authorized_client.post(reverse("add-cafe"), cafe_payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    created = Cafe.objects.get(name=cafe_payload["name"])
    for field, value in cafe_payload.items():
        assert getattr(created, field) == value


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", ""),
        ("name", "x" * 251),
        ("map_url", "not-a-url"),
        ("img_url", "not-a-url"),
        ("has_wifi", "not-a-boolean"),
        ("coffee_price", "-1.00"),
        ("coffee_price", "1.234"),
        ("coffee_price", "$2.00"),
        ("currency", "INVALID"),
        ("currency", ""),
    ],
)
def test_add_cafe_rejects_invalid_fields(authorized_client, cafe_payload, field, value):
    cafe_payload[field] = value
    response = authorized_client.post(reverse("add-cafe"), cafe_payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert field in response.data
    assert not Cafe.objects.exists()


def test_add_cafe_requires_name(authorized_client, cafe_payload):
    del cafe_payload["name"]
    response = authorized_client.post(reverse("add-cafe"), cafe_payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "name" in response.data
    assert not Cafe.objects.exists()


def test_add_cafe_rejects_duplicate_name(authorized_client, cafe, cafe_payload):
    cafe_payload["name"] = cafe.name
    response = authorized_client.post(reverse("add-cafe"), cafe_payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "name" in response.data
    assert Cafe.objects.count() == 1


def test_delete_cafe_persists_deletion(authorized_client, cafe):
    response = authorized_client.delete(reverse("delete-cafe", args=[cafe.pk]))

    assert response.status_code == status.HTTP_200_OK
    assert not Cafe.objects.filter(pk=cafe.pk).exists()


@pytest.mark.parametrize("method,route", [("patch", "update-cafe-price"), ("delete", "delete-cafe")])
def test_write_missing_cafe(authorized_client, cafe, method, route):
    missing_pk = cafe.pk
    cafe.delete()
    response = getattr(authorized_client, method)(
        reverse(route, args=[missing_pk]), {"coffee_price": "3.00"}, format="json"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data == {"error": "Cafe not found."}


@pytest.mark.parametrize(
    "method,route", [("post", "add-cafe"), ("patch", "update-cafe-price"), ("delete", "delete-cafe")]
)
def test_write_rejects_incorrect_api_key(api_client, cafe, cafe_payload, method, route):
    api_client.credentials(HTTP_X_API_KEY="incorrect-key")
    url = reverse(route) if method == "post" else reverse(route, args=[cafe.pk])
    payload = cafe_payload if method == "post" else {"coffee_price": "3.00"}
    response = getattr(api_client, method)(url, payload, format="json")

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "detail" in response.data
    assert Cafe.objects.count() == 1
    cafe.refresh_from_db()
    assert cafe.coffee_price == Decimal("2.50")


def test_add_cafe_requires_currency_with_price(authorized_client, cafe_payload):
    del cafe_payload["currency"]
    response = authorized_client.post(reverse("add-cafe"), cafe_payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "currency" in response.data
    assert not Cafe.objects.exists()


def test_add_cafe_without_price(authorized_client, cafe_payload):
    del cafe_payload["coffee_price"]
    del cafe_payload["currency"]
    response = authorized_client.post(reverse("add-cafe"), cafe_payload, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    created = Cafe.objects.get()
    assert created.coffee_price is None
    assert created.currency == ""


def test_add_cafe_rejects_currency_without_price(authorized_client, cafe_payload):
    cafe_payload["coffee_price"] = None
    response = authorized_client.post(reverse("add-cafe"), cafe_payload, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "coffee_price" in response.data


@pytest.mark.parametrize("price", ["0.00", "3.50", 3.5])
def test_update_price_preserves_currency(authorized_client, cafe, price):
    response = authorized_client.patch(
        reverse("update-cafe-price", args=[cafe.pk]),
        {"coffee_price": price}, format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    cafe.refresh_from_db()
    assert cafe.coffee_price == Decimal(str(price))
    assert cafe.currency == "USD"


def test_update_price_and_currency(authorized_client, cafe):
    response = authorized_client.patch(
        reverse("update-cafe-price", args=[cafe.pk]),
        {"coffee_price": "2500.00", "currency": "ARS"}, format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    cafe.refresh_from_db()
    assert cafe.coffee_price == Decimal("2500.00")
    assert cafe.currency == "ARS"


def test_first_price_requires_currency(authorized_client, cafe):
    cafe.coffee_price = None
    cafe.currency = ""
    cafe.save()
    url = reverse("update-cafe-price", args=[cafe.pk])
    response = authorized_client.patch(url, {"coffee_price": "3.00"}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "currency" in response.data
    cafe.refresh_from_db()
    assert cafe.coffee_price is None

    response = authorized_client.patch(
        url, {"coffee_price": "3.00", "currency": "GBP"}, format="json"
    )
    assert response.status_code == status.HTTP_200_OK
    cafe.refresh_from_db()
    assert cafe.coffee_price == Decimal("3.00")
    assert cafe.currency == "GBP"


@pytest.mark.parametrize("currency", ["", "INVALID"])
def test_update_rejects_invalid_currency(authorized_client, cafe, currency):
    response = authorized_client.patch(
        reverse("update-cafe-price", args=[cafe.pk]),
        {"coffee_price": "3.00", "currency": currency}, format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "currency" in response.data
    cafe.refresh_from_db()
    assert cafe.coffee_price == Decimal("2.50")
    assert cafe.currency == "USD"


@pytest.mark.parametrize(
    "price,currency",
    [("-0.01", "USD"), ("100000000.00", "USD"), ("2.00", ""),
     ("2.00", "XXX"), (None, "USD")],
)
def test_database_rejects_invalid_price_pairs(cafe, price, currency):
    with pytest.raises(IntegrityError), transaction.atomic():
        Cafe.objects.filter(pk=cafe.pk).update(coffee_price=price, currency=currency)

    cafe.refresh_from_db()
    assert cafe.coffee_price == Decimal("2.50")
    assert cafe.currency == "USD"
