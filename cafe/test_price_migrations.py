from decimal import Decimal

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


OLD = ("cafe", "0002_alter_cafe_img_url_alter_cafe_map_url")
NEW = ("cafe", "0003_decimal_coffee_price")


@pytest.fixture
def legacy_cafes(transactional_db):
    executor = MigrationExecutor(connection)
    executor.migrate([OLD])
    model = executor.loader.project_state([OLD]).apps.get_model("cafe", "Cafe")
    try:
        yield model
    finally:
        # Restore the schema even when a rejected legacy value prevents migration.
        executor = MigrationExecutor(connection)
        if NEW not in executor.loader.applied_migrations:
            model.objects.all().delete()
        executor.migrate([NEW])


def create_legacy_cafe(model, name, price):
    return model.objects.create(
        name=name, coffee_price=price, location="London", seats="20",
        map_url="https://example.com/map", img_url="https://example.com/image",
        has_toilet=True, has_wifi=True, has_sockets=False, can_take_calls=False,
    )


def test_price_migration_preserves_amounts_and_unknown_prices(legacy_cafes):
    priced = create_legacy_cafe(legacy_cafes, "Priced", "\u00a32.40")
    empty = create_legacy_cafe(legacy_cafes, "Empty", "")
    unknown = create_legacy_cafe(legacy_cafes, "Unknown", None)
    executor = MigrationExecutor(connection)
    executor.migrate([NEW])
    model = executor.loader.project_state([NEW]).apps.get_model("cafe", "Cafe")

    converted = model.objects.get(pk=priced.pk)
    assert converted.coffee_price == Decimal("2.40")
    assert converted.currency == "GBP"
    for pk in [empty.pk, unknown.pk]:
        converted = model.objects.get(pk=pk)
        assert converted.coffee_price is None
        assert converted.currency == ""

    executor = MigrationExecutor(connection)
    executor.migrate([OLD])
    assert legacy_cafes.objects.get(pk=priced.pk).coffee_price == "\u00a32.40"


@pytest.mark.parametrize("price", ["$3.00", "From 3", "\u00a32.345", "-2.00"])
def test_price_migration_rejects_ambiguous_values(legacy_cafes, price):
    cafe = create_legacy_cafe(legacy_cafes, "Ambiguous", price)
    with pytest.raises(ValueError, match="ambiguous legacy price"):
        MigrationExecutor(connection).migrate([NEW])

    assert legacy_cafes.objects.get(pk=cafe.pk).coffee_price == price
