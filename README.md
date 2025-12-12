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

---

## Scalability & Architecture

### Current Architecture

The application uses a **3-tier architecture**:
1. **API Layer** - FastAPI application handling HTTP requests
2. **Data Layer** - PostgreSQL for relational data, Redis for caching/statistics
3. **Business Logic Layer** - Service classes (BiddingService, StatisticsService)

### Horizontal Scaling Strategy

#### 1. **Application Tier Scaling**

**Load Balancing:**
```
                    ┌──> App Instance 1
Client ──> Load Balancer ──┼──> App Instance 2
                    └──> App Instance 3
```

- **Implementation**: Use Nginx, HAProxy, or cloud load balancers (AWS ALB, GCP Load Balancer)
- **Considerations**:
  - Stateless application design (no session storage in app memory)
  - Shared Redis for rate limiting and statistics
  - Health check endpoints for load balancer monitoring
  - Docker/Kubernetes for container orchestration

**Kubernetes Deployment Example:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: auction-service
spec:
  replicas: 5  # Scale to 5 instances
  selector:
    matchLabels:
      app: auction-service
  template:
    spec:
      containers:
      - name: app
        image: auction-service:latest
        resources:
          requests:
            cpu: "500m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: auction-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: auction-service
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

#### 2. **Database Tier Scaling**

**PostgreSQL Scaling:**

- **Read Replicas**: Create read-only replicas for analytics queries
  ```
  Primary (Write) ──> Read Replica 1 (Analytics)
                 └──> Read Replica 2 (Reporting)
  ```

- **Connection Pooling**: Use PgBouncer to manage database connections efficiently
  ```yaml
  # PgBouncer configuration
  [databases]
  aea_db = host=postgres-primary port=5432 dbname=aea_db

  [pgbouncer]
  pool_mode = transaction
  max_client_conn = 1000
  default_pool_size = 25
  ```

- **Sharding Strategy** (for massive scale):
  - Shard by `supply_id` for supply/bidder data
  - Use PostgreSQL partitioning or tools like Citus
  ```sql
  -- Example: Partition supplies by hash
  CREATE TABLE supplies (
    id TEXT PRIMARY KEY,
    ...
  ) PARTITION BY HASH (id);

  CREATE TABLE supplies_p1 PARTITION OF supplies
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);
  CREATE TABLE supplies_p2 PARTITION OF supplies
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);
  ```

**Redis Scaling:**

- **Redis Cluster**: Distribute data across multiple Redis nodes
  ```yaml
  # Redis Cluster with 6 nodes (3 masters, 3 replicas)
  redis-cluster:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes
    deploy:
      replicas: 6
  ```

- **Separate Redis Instances** by purpose:
  - Redis 1: Rate limiting
  - Redis 2: Statistics/Analytics
  - Redis 3: Caching (optional)

#### 3. **Microservices Architecture** (Future)

Split into specialized services:

```
┌─────────────────┐
│   API Gateway   │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────────┐
    │         │          │              │
┌───▼────┐ ┌──▼──────┐ ┌▼────────┐ ┌───▼──────┐
│ Bidding│ │  Stats  │ │  Rate   │ │  Admin   │
│Service │ │ Service │ │ Limiter │ │ Service  │
└────┬───┘ └──┬──────┘ └┬────────┘ └────┬─────┘
     │        │         │              │
     └────────┴─────────┴──────────────┘
                    │
            ┌───────┴────────┐
            │                │
       ┌────▼─────┐    ┌─────▼────┐
       │PostgreSQL│    │  Redis   │
       └──────────┘    └──────────┘
```

**Benefits:**
- Independent scaling of services
- Fault isolation
- Technology flexibility
- Easier maintenance

#### 4. **Caching Strategy**

**Multi-Level Caching:**

```
Request ──> App Memory Cache (LRU)
              │ miss
              ├──> Redis Cache (TTL: 5min)
              │     │ miss
              │     └──> PostgreSQL
              │           │
              └───────────┘ result cached
```

**Implementation:**
```python
from functools import lru_cache
import redis.asyncio as redis

class CachedSupplyDAO:
    @lru_cache(maxsize=1000)
    async def get_supply_cached(self, supply_id: str):
        # Check Redis first
        cached = await self.redis.get(f"supply:{supply_id}")
        if cached:
            return json.loads(cached)

        # Fallback to database
        supply = await self.get(supply_id)

        # Cache result
        await self.redis.setex(
            f"supply:{supply_id}",
            300,  # 5 minutes TTL
            json.dumps(supply)
        )
        return supply
```

#### 5. **Performance Optimizations**

**Database Indexing:**
```sql
-- Essential indexes for auction queries
CREATE INDEX idx_bidders_country ON bidders(country);
CREATE INDEX idx_supply_bidder_supply ON supply_bidder(supply_id);
CREATE INDEX idx_supply_bidder_bidder ON supply_bidder(bidder_id);

-- Composite index for common queries
CREATE INDEX idx_bidders_country_id ON bidders(country, id);
```

**Async Processing:**
- Use async/await throughout (already implemented)
- Consider message queues (RabbitMQ, Kafka) for non-critical operations
- Background workers for heavy analytics processing

**Connection Pooling:**
```python
# Already configured in session.py
engine = create_async_engine(
    pool_size=20,        # Base connections
    max_overflow=25,     # Extra connections under load
    pool_pre_ping=True,  # Verify connections
    pool_recycle=3600,   # Recycle hourly
)
```

### Load Testing & Monitoring

**Load Testing Tools:**
- **Locust**: Simulate concurrent auction requests
  ```python
  from locust import HttpUser, task, between

  class AuctionUser(HttpUser):
      wait_time = between(0.1, 0.5)

      @task
      def run_auction(self):
          self.client.post("/bid", json={
              "supply_id": "finance_hub",
              "ip": f"192.168.1.{random.randint(1, 255)}",
              "country": "US",
              "tmax": 200
          })
  ```

**Monitoring Stack:**
- **Prometheus**: Metrics collection
- **Grafana**: Dashboards
- **Jaeger/Tempo**: Distributed tracing
- **ELK Stack**: Log aggregation

**Key Metrics to Monitor:**
- Request rate (req/sec)
- Response time (p50, p95, p99)
- Error rate
- Database connection pool usage
- Redis memory usage
- CPU/Memory per instance

### Expected Performance

**Current Architecture (Single Instance):**
- **Throughput**: ~1,000-2,000 req/sec
- **Latency**: <50ms (p95) without tmax delays
- **Bottleneck**: Database queries for supply/bidder lookup

**Scaled Architecture (5 instances + Read Replicas):**
- **Throughput**: ~5,000-10,000 req/sec
- **Latency**: <30ms (p95)
- **Bottleneck**: Redis statistics writes

**Optimized Architecture (10+ instances + Redis Cluster + Caching):**
- **Throughput**: 50,000+ req/sec
- **Latency**: <20ms (p95)
- **Bottleneck**: Network I/O

---

## Analytics Data Storage

### Current Implementation

**Statistics Storage: Redis Hashes**

- **Structure**: Single hash per supply
  ```
  Key: stats:{supply_id}
  Fields:
    - total_reqs: 1000
    - country:US: 600
    - country:GB: 400
    - bidder:bidder1:wins: 150
    - bidder:bidder1:revenue: 75.50
    - bidder:bidder1:no_bids: 200
    - bidder:bidder1:timeouts: 50
  ```

- **Advantages**:
  - ✅ Fast increments (O(1) atomic operations)
  - ✅ Real-time statistics
  - ✅ Low latency (<1ms)
  - ✅ Simple data model

- **Limitations**:
  - ❌ Limited analytical queries
  - ❌ No historical data retention
  - ❌ Memory-bound (Redis RAM)
  - ❌ No aggregations across time periods

### Scalable Analytics Solutions

#### Option 1: **Time-Series Database (Recommended)**

**ClickHouse** - Column-oriented database perfect for analytics:

```sql
-- Events table (append-only)
CREATE TABLE auction_events (
    event_time DateTime,
    supply_id String,
    country String,
    bidder_id String,
    event_type Enum('request', 'bid', 'no_bid', 'timeout', 'win'),
    price Nullable(Float64),

    -- Denormalized for fast queries
    date Date DEFAULT toDate(event_time),
    hour UInt8 DEFAULT toHour(event_time)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (supply_id, date, event_time);

-- Aggregated statistics (materialized view)
CREATE MATERIALIZED VIEW supply_stats_hourly
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (supply_id, date, hour)
AS SELECT
    supply_id,
    date,
    hour,
    count() as total_requests,
    countIf(event_type = 'win') as total_wins,
    sum(price) as total_revenue,
    countIf(event_type = 'no_bid') as total_no_bids,
    countIf(event_type = 'timeout') as total_timeouts
FROM auction_events
GROUP BY supply_id, date, hour;
```

**Query Performance:**
```sql
-- Get last 24 hours statistics - executes in <100ms
SELECT
    supply_id,
    sum(total_requests) as requests,
    sum(total_wins) as wins,
    sum(total_revenue) as revenue
FROM supply_stats_hourly
WHERE date >= today() - 1
GROUP BY supply_id;
```

**Implementation:**
```python
# Write events asynchronously
async def record_auction_event(supply_id, country, bidder_id, event_type, price=None):
    await clickhouse_client.execute(
        """
        INSERT INTO auction_events
        (event_time, supply_id, country, bidder_id, event_type, price)
        VALUES
        """,
        [(datetime.now(), supply_id, country, bidder_id, event_type, price)]
    )
```

**Storage Requirements:**
- ~200 bytes per event
- 1M events/day = ~200 MB/day = ~6 GB/month
- Compress 10:1 ratio = ~600 MB/month

#### Option 2: **Data Warehouse (Big Data)**

**Apache Kafka + Apache Spark + Parquet Files**

```
Auction Events ──> Kafka ──> Spark Streaming ──> Parquet ──> AWS S3/HDFS
                      │                            │
                      │                            └──> Query: Presto/Athena
                      └──> Real-time: Flink ──> Redis (Hot Data)
```

**Benefits:**
- Unlimited historical data
- Complex analytics (ML, predictions)
- Cost-effective for massive scale
- Separate compute from storage

**Example Spark Job:**
```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import window, count, sum as _sum

spark = SparkSession.builder.appName("AuctionAnalytics").getOrCreate()

# Read from Kafka
events = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "auction-events") \
    .load()

# Aggregate by window
windowed_stats = events \
    .groupBy(
        window(events.timestamp, "1 hour"),
        events.supply_id,
        events.country
    ) \
    .agg(
        count("*").alias("total_requests"),
        _sum("price").alias("total_revenue")
    )

# Write to Parquet
windowed_stats \
    .writeStream \
    .format("parquet") \
    .option("path", "s3://analytics-bucket/auction-stats/") \
    .option("checkpointLocation", "s3://analytics-bucket/checkpoints/") \
    .start()
```

#### Option 3: **Hybrid Approach (Best of Both Worlds)**

**Architecture:**
```
Write Path:
  Auction Event ──┬──> Redis (Hot data, last 24h)
                  └──> Kafka ──> ClickHouse (Warm data, last 90 days)
                              └──> S3 Parquet (Cold data, 90+ days)

Read Path:
  Analytics Query ──┬──> Redis (real-time, <1s)
                    ├──> ClickHouse (hourly/daily, <1s)
                    └──> Athena/Presto (historical, <10s)
```

**Implementation:**
```python
class HybridStatisticsService:
    def __init__(self, redis, clickhouse, kafka):
        self.redis = redis
        self.clickhouse = clickhouse
        self.kafka = kafka

    async def record_event(self, event):
        # Write to all stores asynchronously
        await asyncio.gather(
            self.redis.hincrby(...),           # Hot data (real-time)
            self.kafka.produce(...),           # Message queue
            # ClickHouse writes handled by Kafka consumer
        )

    async def get_statistics(self, supply_id, time_range):
        if time_range == "realtime":
            return await self.redis.hgetall(f"stats:{supply_id}")
        elif time_range == "last_30_days":
            return await self.clickhouse.query(...)
        else:  # historical
            return await self.athena.query(...)
```

#### Option 4: **PostgreSQL with Partitioning** (Simple, Lower Scale)

```sql
-- Create partitioned table
CREATE TABLE auction_events (
    id BIGSERIAL,
    event_time TIMESTAMP NOT NULL,
    supply_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    ...
) PARTITION BY RANGE (event_time);

-- Create monthly partitions
CREATE TABLE auction_events_2024_01 PARTITION OF auction_events
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE auction_events_2024_02 PARTITION OF auction_events
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Indexes for fast queries
CREATE INDEX idx_events_supply_time
    ON auction_events (supply_id, event_time DESC);

-- Aggregated statistics table
CREATE TABLE supply_stats_daily (
    supply_id TEXT,
    date DATE,
    total_requests INTEGER,
    total_wins INTEGER,
    total_revenue DECIMAL(10,2),
    PRIMARY KEY (supply_id, date)
);

-- Scheduled aggregation job (run hourly)
INSERT INTO supply_stats_daily
SELECT
    supply_id,
    DATE(event_time) as date,
    COUNT(*) as total_requests,
    COUNT(*) FILTER (WHERE event_type = 'win') as total_wins,
    SUM(price) as total_revenue
FROM auction_events
WHERE event_time >= NOW() - INTERVAL '1 day'
GROUP BY supply_id, DATE(event_time)
ON CONFLICT (supply_id, date)
DO UPDATE SET
    total_requests = EXCLUDED.total_requests,
    total_wins = EXCLUDED.total_wins,
    total_revenue = EXCLUDED.total_revenue;
```

### Data Retention Policies

**Hot Data (Redis):**
- **Retention**: 24 hours
- **Purpose**: Real-time dashboards, instant statistics
- **Cleanup**: TTL on keys or scheduled job

**Warm Data (ClickHouse/PostgreSQL):**
- **Retention**: 90 days
- **Purpose**: Business analytics, reporting
- **Cleanup**: Drop old partitions

**Cold Data (S3/Parquet):**
- **Retention**: 7 years (compliance)
- **Purpose**: Historical analysis, audits
- **Cleanup**: S3 lifecycle policies

**Archival:**
- **Solution**: AWS Glacier, Google Cloud Archive
- **Cost**: ~$1/TB/month
- **Access**: Hours to retrieve

### Cost Comparison

| Solution | Cost/TB/Month | Query Speed | Scale Limit |
|----------|---------------|-------------|-------------|
| Redis | $500-1000 | <1ms | ~100GB |
| PostgreSQL | $50-100 | 10-100ms | ~10TB |
| ClickHouse | $20-50 | 100-500ms | ~100TB+ |
| S3 Parquet | $2-5 | 1-10s | Unlimited |
| Glacier | $1 | Hours | Unlimited |

### Recommended Architecture

**For < 1M events/day:**
- Redis (real-time) + PostgreSQL (analytics)

**For 1-10M events/day:**
- Redis (real-time) + ClickHouse (analytics)

**For 10M+ events/day:**
- Redis (real-time) + Kafka + ClickHouse (warm) + S3 (cold)

---

## Running the Application

See [DOCKER.md](DOCKER.md) for Docker setup and deployment instructions.
