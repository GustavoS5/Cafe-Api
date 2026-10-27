from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

class Cafe(models.Model):
    class Currency(models.TextChoices):
        GBP = "GBP", "British pound"
        USD = "USD", "US dollar"
        EUR = "EUR", "Euro"
        ARS = "ARS", "Argentine peso"

    name = models.CharField(max_length=250, unique=True)
    map_url = models.URLField(max_length=500)
    img_url = models.URLField(max_length=500)
    location = models.CharField(max_length=250)
    seats = models.CharField(max_length=250)
    has_toilet = models.BooleanField()
    has_wifi = models.BooleanField()
    has_sockets = models.BooleanField()
    can_take_calls = models.BooleanField()
    coffee_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    currency = models.CharField(max_length=3, choices=Currency, blank=True, default="")

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(coffee_price__isnull=True, currency="")
                    | models.Q(
                        coffee_price__isnull=False,
                        coffee_price__gte=0, coffee_price__lte=Decimal("99999999.99"),
                        currency__in=["GBP", "USD", "EUR", "ARS"],
                    )
                ),
                name="cafe_valid_price_and_currency",
            ),
        ]

