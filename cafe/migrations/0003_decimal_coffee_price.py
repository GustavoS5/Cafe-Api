import re
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import migrations, models


def convert_prices(apps, schema_editor):
    Cafe = apps.get_model("cafe", "Cafe")
    cafes = Cafe.objects.using(schema_editor.connection.alias)
    for cafe in cafes.all().iterator():
        raw = (cafe.legacy_coffee_price or "").strip()
        if not raw:
            continue
        match = re.fullmatch(r"\u00a3\s*([0-9]{1,8}(?:\.[0-9]{1,2})?)", raw)
        if match is None:
            raise ValueError(f"Cafe {cafe.pk} has an ambiguous legacy price: {raw!r}")
        cafes.filter(pk=cafe.pk).update(coffee_price=Decimal(match[1]), currency="GBP")


def restore_prices(apps, schema_editor):
    Cafe = apps.get_model("cafe", "Cafe")
    cafes = Cafe.objects.using(schema_editor.connection.alias)
    for cafe in cafes.all().iterator():
        price = None
        if cafe.coffee_price is not None:
            prefix = "\u00a3" if cafe.currency == "GBP" else f"{cafe.currency} "
            price = f"{prefix}{cafe.coffee_price:.2f}"
        cafes.filter(pk=cafe.pk).update(legacy_coffee_price=price)


class Migration(migrations.Migration):
    dependencies = [("cafe", "0002_alter_cafe_img_url_alter_cafe_map_url")]

    operations = [
        migrations.RenameField("cafe", "coffee_price", "legacy_coffee_price"),
        migrations.AddField(
            model_name="cafe", name="coffee_price",
            field=models.DecimalField(
                max_digits=10, decimal_places=2, blank=True, null=True,
                validators=[MinValueValidator(Decimal("0.00"))],
            ),
        ),
        migrations.AddField(
            model_name="cafe", name="currency",
            field=models.CharField(
                max_length=3, blank=True, default="",
                choices=[("GBP", "British pound"), ("USD", "US dollar"), ("EUR", "Euro"), ("ARS", "Argentine peso")],
            ),
        ),
        migrations.RunPython(convert_prices, restore_prices),
        migrations.RemoveField("cafe", "legacy_coffee_price"),
        migrations.AddConstraint(
            model_name="cafe",
            constraint=models.CheckConstraint(
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
        ),
    ]
