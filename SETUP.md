# LSHRS Examples - Setup Guide

Complete guide to running the LSHRS demonstration notebooks.

## File Structure

```
docs/examples/
├── docker-compose.yml          # Services: Redis, PostgreSQL, Adminer
├── requirements.txt            # Python dependencies
├── README.md                   # Overview and troubleshooting
├── SETUP.md                    # This file
├── 01_basic_lsh.ipynb         # Core LSH concepts (Beginner)
├── 02_postgres_integration.ipynb  # Production workflow (Intermediate)
└── 03_benchmark.ipynb         # Performance benchmarking (Advanced)
```

## System Requirements

- **Python**: 3.10+
- **Docker**: 20.10+
- **RAM**: 4GB (minimum), 8GB (recommended)
- **Disk**: 2GB free space
- **OS**: Linux, macOS, or Windows (WSL2)

## Installation Steps

### Step 1: Clone & Navigate

```bash
git clone https://github.com/yourusername/lshrs.git
cd lshrs/docs/examples
```

### Step 2: Create Virtual Environment

```bash
# Using venv
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using conda
conda create -n lshrs-demo python=3.10
conda activate lshrs-demo
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Start Services

```bash
# Start Docker containers
docker-compose up -d

# Verify all services are healthy
docker-compose ps

# Expected output:
# NAME              STATUS           PORTS
# examples-redis-1  Up (healthy)     6379/tcp
# examples-db-1     Up (healthy)     5432/tcp
# examples-adminer-1 Up              8080/tcp
```

Wait for health checks to pass (look for "(healthy)" status):
```bash
# Monitor health
docker-compose ps --format "{{.Names}}: {{.State}}"

# Wait up to 30 seconds for startup
sleep 10
```

### Step 5: Verify Connectivity

```bash
# Test Redis
redis-cli -h localhost ping
# Expected: PONG

# Test PostgreSQL
psql postgresql://postgres:changeme@localhost:5432/demo -c "SELECT version();"
# Expected: PostgreSQL version info

# Test pgvector (optional)
psql postgresql://postgres:changeme@localhost:5432/demo -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Step 6: Launch Jupyter

```bash
# Start Jupyter Lab
jupyter lab

# Or Jupyter Notebook
jupyter notebook

# Access: http://localhost:8888
```

## Running the Notebooks

### Recommended Order

#### 1. Basic LSH (01_basic_lsh.ipynb)
- **Prerequisites**: None
- **Duration**: 10-15 minutes
- **Learning**: Core concepts without external dependencies
- **Start here if**: New to LSH

```bash
jupyter lab 01_basic_lsh.ipynb
```

Run all cells sequentially. Expected output:
- Auto-configuration analysis
- Collision analysis with visualization
- Recall/Precision metrics

#### 2. PostgreSQL Integration (02_postgres_integration.ipynb)
- **Prerequisites**: Docker services running
- **Duration**: 15-20 minutes
- **Learning**: Production workflow with real database
- **Start here if**: Want to see end-to-end system

```bash
jupyter lab 02_postgres_integration.ipynb
```

This notebook:
1. Creates PostgreSQL schema
2. Populates 2K product embeddings
3. Streams to LSH index
4. Executes two-stage queries (LSH + rerank)
5. Compares performance

#### 3. Benchmarking (03_benchmark.ipynb)
- **Prerequisites**: Docker services running
- **Duration**: 20-30 minutes
- **Learning**: Performance metrics and SLA validation
- **Start here if**: Need production capacity planning

```bash
jupyter lab 03_benchmark.ipynb
```

This notebook:
1. Benchmarks ingestion (1K, 10K, 100K scales)
2. Measures query latency distributions
3. Tests parameter sensitivity
4. Validates SLA compliance
5. Produces performance report

## Configuration

### Redis Configuration

For large-scale testing, increase Redis memory:

```bash
# Create redis-local.conf
cat > redis-local.conf << EOF
maxmemory 2gb
maxmemory-policy allkeys-lru
save 60 1
appendonly yes
EOF

# Update docker-compose.yml:
# command: redis-server redis-local.conf

docker-compose restart redis
```

### PostgreSQL Configuration

For faster ingestion, adjust connection pool:

```python
# In notebooks, update DB connection:
from sqlalchemy import create_engine, pool

engine = create_engine(
    DB_URL,
    poolclass=pool.QueuePool,
    pool_size=10,
    max_overflow=20
)
```

### Vector Dimension

Change vector dimension in notebooks (defaults: 256, 128):

```python
DIM = 512  # Larger = more realistic, slower
```

## Troubleshooting

### Issue: "redis.exceptions.ConnectionError"

**Cause**: Redis not running or not accessible

**Solution**:
```bash
# Check if container is running
docker-compose ps redis

# Start if stopped
docker-compose up -d redis

# Test connection
redis-cli -h localhost ping

# Check logs
docker-compose logs redis
```

### Issue: "psycopg2.OperationalError: could not connect"

**Cause**: PostgreSQL not ready

**Solution**:
```bash
# Wait for PostgreSQL startup
docker-compose logs db

# Restart PostgreSQL
docker-compose restart db

# Test connection
psql postgresql://postgres:changeme@localhost:5432/demo -c "SELECT 1;"

# View connection string in Adminer: http://localhost:8080
```

### Issue: "ModuleNotFoundError: No module named 'lshrs'"

**Cause**: LSHRS not installed

**Solution**:
```bash
# Install from source
cd ../..
pip install -e .

# Or from PyPI
pip install lshrs
```

### Issue: "Out of memory" during benchmark

**Cause**: 100K vector benchmark too large

**Solution**:
```python
# Reduce vector count in 03_benchmark.ipynb
# Change: N_VECTORS = 100_000
# To: N_VECTORS = 50_000  # Or smaller

# Or increase Docker memory:
# Edit docker-compose.yml:
# services:
#   redis:
#     environment:
#       - REDIS_MAXMEMORY=4gb
```

### Issue: Slow ingestion (<1K vectors/sec)

**Cause**: Small batch size or slow network

**Solution**:
```python
# Increase batch size in notebooks
lsh.create_signatures(..., batch_size=5000)

# Or use direct batch API
lsh.index(ids, vectors)  # Better than create_signatures for local data

# Check Redis connection
redis-cli --latency
```

## Monitoring

### Real-time Resource Usage

```bash
# Watch Redis memory
watch -n 1 'redis-cli info memory'

# Watch PostgreSQL connections
watch -n 1 'psql postgresql://postgres:changeme@localhost:5432/demo -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;"'

# Docker stats
docker stats --no-stream
```

### Adminer UI

Visit http://localhost:8080:
- **System**: PostgreSQL
- **Server**: db
- **Username**: postgres
- **Password**: changeme
- **Database**: demo

Then browse products table and embeddings.

## Performance Tips

### For Faster Notebooks

1. **Skip 100K benchmark** (takes 5+ minutes):
   - Edit `03_benchmark.ipynb`
   - Comment out large index test
   - Focus on 1K and 10K

2. **Reduce vector counts**:
   - `02_postgres_integration.ipynb`: Change `NUM_PRODUCTS = 2000` → `500`
   - `03_benchmark.ipynb`: Change `N_VECTORS = 100_000` → `50_000`

3. **Use smaller vector dimension**:
   - Change `DIM = 256` → `128`
   - Reduces computation by 4x

### For Production Validation

1. **Use your actual vectors**: Replace synthetic data with real embeddings
2. **Test your scale**: Use expected index size
3. **Tune parameters**: Run `03_benchmark.ipynb` with your config
4. **Monitor latency**: Collect baseline metrics

## Cleaning Up

### Stop Services

```bash
# Stop containers (data persists)
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove all data (volumes)
docker-compose down -v
```

### Reset Notebooks

```bash
# Clear cell outputs
jupyter nbconvert --ClearMetadataPreprocessor.enabled=True --inplace *.ipynb

# Or in Jupyter: Kernel → Restart & Clear Output
```

## Next Steps

1. **Integrate into your app**:
   ```python
   from lshrs import LSHRS
   
   lsh = LSHRS(
       dim=your_dim,
       similarity_threshold=0.7,
       vector_fetch_fn=your_fetch,
       redis_host="your-redis"
   )
   ```

2. **Customize for your data**:
   - Update database schema
   - Modify vector source
   - Adjust batch sizes

3. **Deploy to production**:
   - Use Kubernetes + Persistent Redis
   - Configure separate indices per tenant
   - Set up monitoring and alerting

## Support

- **Documentation**: See [README.md](README.md)
- **Issues**: Report on GitHub
- **Questions**: Check [LSHRS Docs](../docs.md)

## Quick Reference

| Task | Command |
|------|---------|
| Start services | `docker-compose up -d` |
| Stop services | `docker-compose stop` |
| View logs | `docker-compose logs -f redis` |
| Launch Jupyter | `jupyter lab` |
| Run single notebook | `jupyter nbconvert --to notebook --execute 01_basic_lsh.ipynb` |
| Reset Redis | `docker-compose restart redis` |
| Open Adminer | http://localhost:8080 |
| Test Redis | `redis-cli ping` |
| Test PostgreSQL | `psql postgresql://postgres:changeme@localhost:5432/demo -c "SELECT 1;"` |
