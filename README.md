# Cafe API

A REST API for cafe listings, built with Django, Django REST Framework, and SQLite. Supports location search, random cafe selection, and API-key-protected writes.

## Setup

Requires Python 3.12 or newer. From the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install ".[dev]"
Copy-Item .env.example .env
```

On macOS/Linux, activate with `source .venv/bin/activate` and copy the configuration with `cp .env.example .env`.

Set these values in `.env` before starting:

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Django secret key; replace the placeholder with a random value |
| `DJANGO_DEBUG` | Enable debug mode for local development only |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hostnames |
| `CAFE_API_KEY` | Key required for write requests; replace the placeholder |

Generate a Django secret key with:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Existing environment variables take precedence over `.env` values. The local configuration and SQLite database are excluded from version control.

```powershell
python manage.py migrate
python manage.py runserver
```

The API runs at `http://127.0.0.1:8000`. The database starts empty; create cafes through `POST /add/`.

## Endpoints

| Method | Path | Description | API Key |
| --- | --- | --- | --- |
| GET | `/all/` | List cafes | No |
| GET | `/random/` | Return a random cafe | No |
| GET | `/search/?loc=Buenos` | Case-insensitive location search | No |
| POST | `/add/` | Create a cafe | Yes |
| PATCH | `/update-price/<id>/` | Update a cafe's price | Yes |
| DELETE | `/delete/<id>/` | Delete a cafe | Yes |

Write requests require the `X-API-KEY` header. A global DRF permission policy allows public reads and rejects writes with missing or incorrect keys with `403` and a `detail` error field. Invalid input returns `400`; missing cafes and empty list/search results return `404`. Collection responses are currently unpaginated.

### Create a Cafe

Send the following JSON to `POST /add/` with `Content-Type: application/json` and `X-API-KEY: <your-key>`:

```json
{
  "name": "Central Cafe",
  "map_url": "https://maps.example.com/central-cafe",
  "img_url": "https://images.example.com/central-cafe.jpg",
  "location": "Buenos Aires",
  "seats": "20-30",
  "has_toilet": true,
  "has_wifi": true,
  "has_sockets": true,
  "can_take_calls": false,
  "coffee_price": "3.00",
  "currency": "USD"
}
```

Names must be unique. Prices are nonnegative decimal amounts with at most two decimal places, up to `99999999.99`. Supported currencies are `GBP`, `USD`, `EUR`, and `ARS`; a currency is required when a price is supplied. To leave the price unknown, omit both fields or send `coffee_price: null` without a currency.

Responses represent decimal amounts as strings, such as `"3.00"`, to preserve precision. Currency symbols are not accepted in price input.

### Update a Price

```sh
curl -X PATCH http://127.0.0.1:8000/update-price/1/ \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: <your-key>" \
  -d '{"coffee_price": "3.50"}'
```

Price updates require a non-null amount. The existing currency is retained unless `currency` is supplied; setting a previously unknown price requires a currency. Other cafe fields are ignored by this endpoint.

The price migration converts legacy pound-prefixed prices to decimal amounts with `GBP`. It stops on unrecognized values instead of guessing a currency or discarding data.

## Tests

```powershell
python -m pytest
```

Tests use pytest-django and DRF's API client with an isolated test database. They cover read endpoints, creation and deletion, price validation, and API-key protection.
