import os
import re
import sqlite3
from decimal import Decimal
import django
from django.db import transaction

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cafe_api.settings")
django.setup()

from cafe.models import Cafe

old_db_path = "instance/cafes.db"

connection = sqlite3.connect(old_db_path)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

cursor.execute("SELECT * FROM cafe")
rows = cursor.fetchall()

with transaction.atomic():
    for row in rows:
        raw_price = (row["coffee_price"] or "").strip()
        match = re.fullmatch(r"\u00a3\s*([0-9]{1,8}(?:\.[0-9]{1,2})?)", raw_price)
        if raw_price and match is None:
            raise ValueError(f"Cafe {row['id']} has an ambiguous price: {raw_price!r}")
        price = Decimal(match[1]) if match else None
        Cafe.objects.update_or_create(
            id=row["id"],
            defaults={
                "name": row["name"],
                "map_url": row["map_url"],
                "img_url": row["img_url"],
                "location": row["location"],
                "seats": row["seats"],
                "has_toilet": bool(row["has_toilet"]),
                "has_wifi": bool(row["has_wifi"]),
                "has_sockets": bool(row["has_sockets"]),
                "can_take_calls": bool(row["can_take_calls"]),
                "coffee_price": price,
                "currency": "GBP" if price is not None else "",
            },
        )

connection.close()
print(f"Imported {len(rows)} cafes")
