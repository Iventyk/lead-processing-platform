# Lead Processing Platform

Backend platform for receiving and processing leads using **two independent FastAPI microservices** in one repository:

- `landings` — receives leads from landing pages and pushes them to a Redis queue.
- `core` — returns analytics for processed leads.
- `worker` — background consumer that reads the Redis queue, applies deduplication, and stores leads in PostgreSQL.

Services communicate with each other only through Redis.

---

## Tech Stack

- Python 3.11+
- FastAPI
- PostgreSQL
- SQLAlchemy 2 + asyncpg
- Alembic
- Redis
- JWT (Bearer)
- Docker / Docker Compose

---

## Architecture

```text
[Landing client]
      |
      | POST /lead (Bearer JWT)
      v
[landings service] --LPUSH--> [Redis queue] --BLPOP--> [worker]
                                                       |
                                                       v
                                                   [PostgreSQL]
                                                       ^
                                                       |
                                   GET /leads (Bearer JWT)
                                                       |
                                                 [core service]
```

### Docker Compose Services

- `postgres` — database
- `redis` — queue broker
- `migrate` — Alembic migrations (`upgrade head`)
- `landings` — lead intake API (port `8001`)
- `core` — analytics API (port `8002`)
- `worker` — background lead processor

---

## Data Model

Three required tables are used:

1. `offers`
   - `id` (PK)
   - `name`

2. `affiliates`
   - `id` (PK)
   - `name`

3. `leads`
   - `id` (PK)
   - `name`
   - `phone`
   - `country` (ISO 3166-1 alpha-2)
   - `offer_id` (FK -> offers.id)
   - `affiliate_id` (FK -> affiliates.id)
   - `created_at` (timestamp when the lead is added to DB)

---

## Authentication & Authorization

All endpoints in both `landings` and `core` require a Bearer JWT.

### JWT payload format

```json
{"id": <affiliates.id>}
```

### Validation rules

- Token must be valid and signed with the same `JWT_SECRET`.
- `id` from token must exist in the `affiliates` table.
- If `affiliates.id` does not exist, API returns `401`.

A helper script is included to generate a test token:

```bash
python tests/generate_token.py
```

> The script uses `{"id": 1}` by default, so ensure an affiliate with `id=1` exists in DB.

---

## API

## 1) Landings Service

Base URL: `http://localhost:8001`

### `POST /lead`

Receives a lead from a landing page, validates fields, checks that `affiliate_id` in request body matches JWT `id`, and queues the payload in Redis.

#### Request body

```json
{
  "name": "Oleksii",
  "phone": "+380982342123",
  "country": "UA",
  "offer_id": 1,
  "affiliate_id": 1
}
```

#### Validation

- `name`: string, 1..255
- `phone`: string, 5..32
- `country`: regex `^[A-Z]{2}$`
- `offer_id`: int, must exist in `offers`
- `affiliate_id`: int, must match `id` from JWT

#### Success response

```json
{"status": "queued"}
```

---

## 2) Core Service

Base URL: `http://localhost:8002`

### `GET /leads`

Returns lead analytics for the affiliate identified by Bearer token.

#### Query params

- `date_from` (`YYYY-MM-DD`)
- `date_to` (`YYYY-MM-DD`)
- `group` (`date` | `offer`)

#### Grouping logic

- `group=date` — groups leads by each day in range.
- `group=offer` — groups leads by offer.

Each bucket includes:
- `count`
- `leads` (detailed list)

---

## Worker Processing & Deduplication

`worker` reads queue messages from Redis and validates before persisting:

1. `offer_id` exists in `offers`
2. `affiliate_id` exists in `affiliates`
3. Deduplication check for same:
   - `name`
   - `phone`
   - `offer_id`
   - `affiliate_id`

If an identical lead was already processed within the last **10 minutes**, the new one is skipped.

Implementation detail: dedup uses Redis key with TTL = `600` seconds.

---

## Run with Docker

### 1. Clone and enter project

```bash
git clone <repo-url>
cd lead-processing-platform
```

### 2. Start all services

```bash
docker compose up --build
```

After startup:

- Landings API: `http://localhost:8001`
- Core API: `http://localhost:8002`
- Landings Swagger: `http://localhost:8001/docs`
- Core Swagger: `http://localhost:8002/docs`

---

## Prepare Seed Data

After migrations are applied, create at least one affiliate and one offer.

Example (via psql):

```sql
INSERT INTO affiliates (name) VALUES ('Affiliate #1');
INSERT INTO offers (name) VALUES ('Offer #1');
```

> Usually the first inserts get `id=1`.

---

## Quick E2E Example

### 1) Generate JWT

```bash
python tests/generate_token.py
```

### 2) Send lead to `landings`

```bash
curl -X POST 'http://localhost:8001/lead' \
  -H 'Authorization: Bearer <TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Oleksii",
    "phone": "+380982342123",
    "country": "UA",
    "offer_id": 1,
    "affiliate_id": 1
  }'
```

### 3) Request analytics from `core`

```bash
curl 'http://localhost:8002/leads?date_from=2026-04-01&date_to=2026-04-30&group=date' \
  -H 'Authorization: Bearer <TOKEN>'
```

---

## Quality & Developer Checks

The project includes:

- `black`
- `flake8`
- `mypy`

Example commands:

```bash
black --check .
flake8
mypy src
```

---