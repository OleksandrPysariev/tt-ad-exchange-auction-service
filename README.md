# tt-ad-exchange-auction-service
Implement a simplified Ad Exchange Auction Service that simulates real-time bidding between multiple bidders based on supply and targeting data. Application must work fast with minimum response delay

## CLI Commands

### generate-input-json
Generates static JSON database file with supplies (publishers/SSPs) and bidders (DSPs/ad networks).

**Usage:**
```bash
python -m app.cli [OPTIONS]
```

**Parameters:**
- `--output, -o PATH` - Output file path (default: `data.json`)
- `--supplies, -s INTEGER` - Number of supplies to generate (default: 10, max: 20)
- `--bidders, -b INTEGER` - Number of bidders to generate (default: 12, max: 20)

**Output Structure:**
```json
{
  "supplies": {
    "supply_name": ["bidder1", "bidder2"]
  },
  "bidders": {
    "bidder_name": {"country": "US"}
  }
}
```

**Examples:**
```bash
# Generate with defaults
python -m app.cli generate-input-json

# Custom output and counts
python -m app.cli generate-input-json --output auction-data.json --supplies 10 --bidders 15
```

### load-data
Load data from JSON file into database tables.

**Usage:**
```bash
python -m app.cli load-data [OPTIONS]
```

**Parameters:**
- `--input, -i PATH` - Path to JSON file (default: `data.json`)

**Examples:**
```bash
# Load from default file
python -m app.cli load-data

# Load from custom file
python -m app.cli load-data --input custom-data.json
```

## Database Management

### Alembic Migrations

**Create a new migration:**
```bash
alembic revision --autogenerate -m "Description of changes"
```

**Apply migrations:**
```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Downgrade one version
alembic downgrade -1
```

**Check current migration status:**
```bash
alembic current
```

**View migration history:**
```bash
alembic history
```

**Downgrade to specific revision:**
```bash
alembic downgrade <revision_id>
```

## Setup

### Dependencies
- FastAPI
- Pydantic-settings
- Alembic
- SQLAlchemy
- Typer
