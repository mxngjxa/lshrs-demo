# LSHRS Examples & Benchmarks

This directory contains comprehensive Jupyter notebooks demonstrating LSHRS functionality with real-world scenarios and production-grade benchmarking.

# Sample output for M3 MacBook Air running `temp.py`. 

📊 Billion-Scale Projections (Single Node)
==========================================
Estimated Indexing Time: 321.7 hours (13.4 days)
Required RAM (Vectors):  ~477 GB
Required Redis Memory:   ~745 GB (Keys + Structures)

Measuring Baseline Query Latency (at 1M scale)...
Avg Latency (1M scale): 15.22 ms
Projected Latency (1B scale): ~228 ms

NOTE: To maintain <100ms at 1B scale, you would need to increase 'rows_per_band'
to make buckets sparser, or distribute Redis across multiple nodes (Sharding).
Done.

## Quick Start

### Prerequisites

```bash
# 1. Clone repository
git clone <repo>
cd docs/examples

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start services
docker-compose up -d

# 4. Verify services
docker-compose ps
```

### Access Points

- **Jupyter**: Run notebooks locally or via `jupyter lab`
- **PostgreSQL/Adminer**: http://localhost:8080 (user: `postgres`, password: `changeme`)
- **Redis**: `localhost:6379`

---

## Notebooks Overview

### 01_basic_lsh.ipynb - Core Concepts

**Duration**: 10-15 minutes | **Complexity**: Beginner

Learn fundamental LSH mechanics without external dependencies.

**Topics Covered**:
- LSH configuration and auto-tuning
- Vector hashing and bucket management
- Similarity search with collision analysis
- Understanding recall vs precision trade-offs
- Visualizing false positives

**Key Takeaways**:
- How random projections create hash signatures
- Band configuration impacts on performance
- Why LSH has probabilistic collisions
- When to use top-K vs top-P queries

**Use Cases**:
- Understanding LSH internals
- Learning configuration parameters
- Debugging unexpected results

---

### 02_postgres_integration.ipynb - Production Workflow

**Duration**: 15-20 minutes | **Complexity**: Intermediate

Build a production-grade system with PostgreSQL and two-stage retrieval.

**Architecture**:
```
PostgreSQL (2K products)
    ↓
[Streaming Iterator]
    ↓
LSHRS [Hashing]
    ↓
Redis [Hot Index]
    ↓
Query Pipeline:
├─ Stage 1: LSH Lookup (Fast)
└─ Stage 2: Cosine Reranking (Accurate)
```

**Topics Covered**:
- Streaming vectors from PostgreSQL
- Batch indexing pipeline
- Two-stage search: LSH + Reranking
- Performance analysis (LSH vs LSH+Rerank)
- Category-specific indexed subsets

**Key Metrics**:
- Indexing throughput: ~5K-10K vectors/sec
- LSH query latency: <10ms (approximate)
- Rerank latency: 5-50ms (accurate)
- End-to-end throughput: Scales linearly

**Use Cases**:
- E-commerce product similarity
- Content recommendation systems
- Document clustering
- Real-time search applications

---

### 03_benchmark.ipynb - Performance Validation

**Duration**: 20-30 minutes | **Complexity**: Advanced

Comprehensive benchmarking across dataset sizes with SLA validation.

**Scenarios**:
1. **Small** (1K vectors): Baseline
2. **Medium** (10K vectors): Typical production
3. **Large** (100K vectors): Stress test

**Metrics Collected**:
- Ingestion throughput (vectors/sec)
- Query latency: mean, p50, p95, p99
- Scalability curves
- Parameter sensitivity analysis
- SLA compliance report

**SLA Targets**:
- Query p95 latency: <100ms
- Query p99 latency: <200ms
- Throughput: >5K vectors/sec
- Linear scalability to 100K+ vectors

**Key Findings**:
- Performance remains sub-100ms at 100K scale
- Throughput scales with batch size
- Lower thresholds trade recall for speed
- Parameter sensitivity: Threshold > Batch Size > Vector Dim

**Use Cases**:
- Pre-deployment validation
- Capacity planning
- SLA enforcement
- Performance regression testing

---

## Requirements.txt

```txt
numpy>=1.21.0
pandas>=1.5.0
scipy>=1.9.0
matplotlib>=3.5.0
jupyter>=1.0.0
psycopg2-binary>=2.9.0
sqlalchemy>=2.0.0
redis>=4.5.0
lshrs>=0.1.0
```

---

## Dataset Specifications

### Example 1 (Basic)
- **Vectors**: 150 (1 anchor + 50 similar + 100 dissimilar)
- **Dimension**: 256
- **Time**: <1 second

### Example 2 (Postgres)
- **Vectors**: 2,000 products
- **Categories**: 5 (electronics, clothing, books, home, sports)
- **Dimension**: 128
- **Storage**: PostgreSQL
- **Time**: 2-5 seconds

### Example 3 (Benchmark)
- **Vectors**: 1K, 10K, 100K
- **Dimension**: 256
- **Queries**: 100 per scale
- **Duration**: 5-10 minutes (100K is slowest)

---

## Troubleshooting

### "Connection refused" on Redis/Postgres

```bash
# Check if containers are running
docker-compose ps

# Restart services
docker-compose down
docker-compose up -d

# Wait for health checks
sleep 10
```

### Slow Ingestion (<1K v/s)

This is normal if:
- Redis is on a slow connection
- Vector dimension is very large (>1K)
- Batch size is small (<100)

**Optimization**:
```python
# Increase batch size
lsh.create_signatures(..., batch_size=5000)

# Or use direct indexing
lsh.index(ids, vectors)  # Batch API
```

### High Query Latency (>100ms)

Check:
1. Index size (100K vs 1K has similar latency due to LSH)
2. Similarity threshold (higher = more candidates = slower)
3. System load (CPU/Memory usage)

### Connection to Postgres Fails

```bash
# Test connection
psql postgresql://postgres:changeme@localhost:5432/demo

# Check container logs
docker-compose logs db
```

---

## Performance Tips

### For Indexing
1. Use batch indexing (not single ingest)
2. Increase batch size (1K-5K ideal)
3. Pre-allocate Redis memory: `redis.conf: maxmemory 2gb`

### For Queries
1. Use LSH-only for speed (<10ms)
2. Use reranking for accuracy (<50ms total)
3. Cache frequent queries

### Configuration Tuning
| Goal | Setting |
|------|---------|
| High Recall | Lower `similarity_threshold` (0.5) |
| High Precision | Higher `similarity_threshold` (0.8) |
| Fast Indexing | Larger `batch_size` (5000) |
| Fast Queries | More `rows_per_band` (less `num_bands`) |

---

## Expected Results

### Example 1: Basic LSH
- Recall: 60-80% (depends on similarity_threshold)
- Precision: 40-70% (LSH produces some false positives)
- Query Time: <1ms

### Example 2: Postgres Integration
- Indexing: 2-5 seconds (2K vectors)
- LSH Query: 5-10ms
- Rerank Query: 10-50ms
- Category filtering: +200ms (SQL overhead)

### Example 3: Benchmark
| Index Size | Throughput | Query p95 |
|------------|-----------|----------|
| 1K | 8,000 v/s | 3.5ms |
| 10K | 7,500 v/s | 4.2ms |
| 100K | 6,500 v/s | 5.8ms |

---

## Next Steps

1. **Integrate into your application**:
   ```python
   from lshrs import LSHRS
   
   lsh = LSHRS(
       dim=your_embedding_dim,
       similarity_threshold=0.7,
       vector_fetch_fn=your_fetch_function,
       redis_host="your_redis_host"
   )
   ```

2. **Deploy to production**:
   - Use Kubernetes with persistent Redis
   - Set `redis_prefix` for multi-tenancy
   - Monitor latency with `get_above_p(p=0.05)`

3. **Optimize for your scale**:
   - Run benchmark notebook with your data
   - Adjust `num_perm` and threshold
   - Profile with `cProfile` for bottlenecks

---

## References

- [LSHRS Documentation](../docs.md)
- [Locality Sensitive Hashing Paper](https://en.wikipedia.org/wiki/Locality-sensitive_hashing)
- [Redis Best Practices](https://redis.io/docs/management/optimization/)
- [PyTorch LSH Implementation](https://github.com/rapidsai/cugraph)

---

## Support

- **Issues**: Report via GitHub
- **Questions**: Check [LSHRS Docs](../docs.md)
- **Performance**: Run `03_benchmark.ipynb` and share results
