from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from cafe.models import Cafe


@pytest.fixture
def api_client(settings):
    settings.API_KEY = "test-api-key"
    return APIClient()


@pytest.fixture
def authorized_client(api_client, settings):
    api_client.credentials(HTTP_X_API_KEY=settings.API_KEY)
    return api_client


@pytest.fixture
def cafe_payload():
    return {
        "name": "New Cafe",
        "map_url": "https://maps.example.com/new-cafe",
        "img_url": "https://images.example.com/new-cafe.jpg",
        "location": "Cordoba",
        "seats": "10-20",
        "has_toilet": True,
        "has_wifi": True,
        "has_sockets": False,
        "can_take_calls": False,
        "coffee_price": Decimal("2.00"),
        "currency": "USD",
    }


@pytest.fixture
def cafe(db):
    return Cafe.objects.create(
        name="Test Cafe",
        map_url="https://maps.example.com/test-cafe",
        img_url="https://images.example.com/test-cafe.jpg",
        location="Buenos Aires",
        seats="20-30",
        has_toilet=True,
        has_wifi=True,
        has_sockets=True,
        can_take_calls=False,
        coffee_price=Decimal("2.50"),
        currency="USD",
    )
