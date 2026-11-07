from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("cafe", "0002_alter_cafe_img_url_alter_cafe_map_url")]

    operations = [
        migrations.RemoveField("cafe", "coffee_price"),
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
