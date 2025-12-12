# tt-ad-exchange-auction-service
Implement a simplified Ad Exchange Auction Service that simulates real-time bidding between multiple bidders based on supply and targeting data. Application must work fast with minimum response delay

## Quick Start

**Docker (recommended):**
```bash
docker-compose up -d
docker-compose exec app alembic upgrade head
docker-compose exec app python -m app.cli load-data
```

**Local:**
```bash
uv sync
uv run alembic upgrade head
uv run python -m app.cli load-data
uv run fastapi dev app/main.py
```

**Verify:** Visit http://localhost:8000/api/docs. Check health at http://localhost:8000 or run `curl http://localhost:8000/supplies` to see available supplies.

## API Endpoints

The service exposes three main endpoints for auction operations and monitoring.

### GET /supplies

Retrieves all available supply IDs that can be used in auction requests.

**Example Request:**
```bash
curl http://localhost:8000/supplies
```

**Example Response:**
```json
[
  {"id": "supply1"},
  {"id": "supply2"},
  {"id": "supply3"}
]
```

**Use Case:** Call this endpoint first to discover available supply IDs before submitting bid requests.

---

### POST /bid

Starts a new auction for a given supply with rate limiting.

**Rate Limiting:** Maximum 3 requests per minute per IP address.

**Example Request:**
```bash
curl -X POST http://localhost:8000/bid \
  -H "Content-Type: application/json" \
  -d '{
    "supply_id": "supply1",
    "ip": "192.168.1.100",
    "country": "US",
    "tmax": 200
  }'
```

**Example Response:**
```json
{
  "winner": "bidder2",
  "price": 0.83
}
```

**Possible HTTP Status Codes:**
- `200 OK` - Auction completed successfully
- `400 Bad Request` - Invalid supply ID or no eligible bidders
- `429 Too Many Requests` - Rate limit exceeded (3 requests/min per IP)

**How the Auction Works:**
1. Validates that the supply exists in the database
2. Filters eligible bidders by country using SQL
3. Simulates bidder responses with random latency (0 to 1.5x `tmax`)
4. Tracks timeouts (when latency > `tmax`)
5. Generates random bid prices ($0.01-$1.00) with 30% no-bid probability
6. Selects the highest bid as the winner
7. Records statistics in Redis

---

### GET /stat

Retrieves auction statistics for all supplies.

**Example Request:**
```bash
curl http://localhost:8000/stat
```

**Example Response:**
```json
{
  "supply1": {
    "total_reqs": 150,
    "reqs_per_country": {
      "US": 75,
      "GB": 50,
      "FR": 25
    },
    "bidders": {
      "bidder1": {
        "wins": 25,
        "total_revenue": 18.45,
        "no_bids": 10,
        "timeouts": 5
      },
      "bidder2": {
        "wins": 30,
        "total_revenue": 22.67,
        "no_bids": 8,
        "timeouts": 2
      }
    }
  },
  "supply2": {
    "total_reqs": 120,
    "reqs_per_country": {
      "US": 60,
      "GB": 60
    },
    "bidders": {
      "bidder3": {
        "wins": 40,
        "total_revenue": 35.20,
        "no_bids": 15,
        "timeouts": 0
      }
    }
  }
}
```

**Data Storage:** Statistics are stored in Redis using hash structures (`stats:{supply_id}`) with atomic increment operations for high performance.

---

## Database Management

### Alembic Migrations

**Create a new migration:**
```bash
# Local
uv run alembic revision --autogenerate -m "Description of changes"

# Docker
docker-compose exec app alembic revision --autogenerate -m "Description of changes"
```

**Apply migrations:**
```bash
# Local - Upgrade to latest
uv run alembic upgrade head

# Docker - Upgrade to latest
docker-compose exec app alembic upgrade head

# Upgrade one version
uv run alembic upgrade +1
docker-compose exec app alembic upgrade +1

# Downgrade one version
uv run alembic downgrade -1
docker-compose exec app alembic downgrade -1
```

**Check current migration status:**
```bash
# Local
uv run alembic current

# Docker
docker-compose exec app alembic current
```

**View migration history:**
```bash
# Local
uv run alembic history

# Docker
docker-compose exec app alembic history
```

**Downgrade to specific revision:**
```bash
# Local
uv run alembic downgrade <revision_id>

# Docker
docker-compose exec app alembic downgrade <revision_id>
```

## Setup

### Dependencies
- FastAPI
- Pydantic-settings
- Alembic
- SQLAlchemy
- Typer

---

## Scalability

Scale horizontally: deploy multiple app instances behind load balancer (Nginx/AWS ALB). Use PostgreSQL read replicas for queries. Deploy Redis Cluster for distributed caching.

## Analytics Data Storage

Stream events to ClickHouse or Kafka -> S3.
