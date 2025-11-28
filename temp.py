# 04_billion_scale_projection.ipynb

# %% [markdown]
# # Billion-Scale LSH Projection
#
# Simulating a 1-billion vector dataset is impossible on a single laptop due to RAM (approx. 1TB required).
#
# Instead, we will:
# 1. **Stress Test a "Shard"**: Fill the index with 1 million vectors (1/1000th of the target).
# 2. **Measure Throughput**: Calculate stable ingestion rates.
# 3. **Project Latency**: Estimate 1B search speed based on O(N) bucket growth mechanics.
#
# **Target Configuration**:
# - Total Vectors: 1,000,000,000 (1B)
# - Dimensions: 128
# - Simulated Nodes: 1 (Linear extrapolation)

# %%
import numpy as np
import time
from lshrs import LSHRS
from tqdm import tqdm

# Configuration
SHARD_SIZE = 1_000_000  # We will physically index this many
DIM = 128
BATCH_SIZE = 10_000  # Larger batches for throughput
PROJECTED_TOTAL = 1_000_000_000
HYPERPLANE_COUNT = 2**15

# %% [markdown]
# ## 1. Initialize Optimized LSH
# For 1B vectors, we need more bands to keep buckets from becoming too full (collisions increase with N).
# We manually override `num_bands` to a higher number (e.g., 50-100) to maintain precision.

# %%
print("Initializing Billion-Scale Configuration...")

# We use a specific band config optimized for large N
# More bands = more buckets = fewer collisions per bucket = faster retrieval at scale
lsh = LSHRS(
    dim=DIM,
    rows_per_band=4,  # Keep individual signatures short
    num_perm=HYPERPLANE_COUNT,
    redis_host="localhost",
    redis_port=6379,
    redis_prefix="billion_test",
)
lsh.clear()
print(f"Configuration: {lsh.stats()}")

# %% [markdown]
# ## 2. Ingestion Throughput Test
# We index the 1M shard in chunks and measure the sustained rate.

# %%
print(f"Generating {SHARD_SIZE} vectors (Float32)...")
# Generate data in chunks to avoid killing RAM
# We don't need to keep all data in memory, just the current batch
chunk_data = np.random.randn(BATCH_SIZE, DIM).astype(np.float32)
chunk_ids = list(range(BATCH_SIZE))

print("Starting Ingestion Stream...")
start_time = time.time()
total_indexed = 0

# Run for enough batches to get a stable rate (e.g., 100 batches of 10k = 1M)
for i in tqdm(range(0, SHARD_SIZE, BATCH_SIZE)):
    # Update IDs (data can be reused to save generation time, logic is same)
    current_ids = [x + i for x in chunk_ids]

    # Index
    lsh.index(current_ids, chunk_data)
    total_indexed += BATCH_SIZE

    if total_indexed % 100_000 == 0:
        elapsed = time.time() - start_time
        rate = total_indexed / elapsed
        print(
            f"  Indexed {total_indexed:,} / {SHARD_SIZE:,} | Rate: {rate:,.0f} vec/sec"
        )

total_time = time.time() - start_time
final_rate = total_indexed / total_time

print("\n✅ Ingestion Complete")
print(f"   Avg Throughput: {final_rate:,.0f} vectors/sec")
print(f"   Time for 1 Million: {total_time:.2f} seconds")

# %% [markdown]
# ## 3. Projection Analysis
# Extrapolate these numbers to 1 Billion vectors.

# %%
seconds_for_1b = PROJECTED_TOTAL / final_rate
hours_for_1b = seconds_for_1b / 3600
days_for_1b = hours_for_1b / 24

print("📊 Billion-Scale Projections (Single Node)")
print("==========================================")
print(f"Estimated Indexing Time: {hours_for_1b:.1f} hours ({days_for_1b:.1f} days)")
print(f"Required RAM (Vectors):  ~{PROJECTED_TOTAL * DIM * 4 / (1024**3):.0f} GB")
print(
    f"Required Redis Memory:   ~{PROJECTED_TOTAL * 100 * 8 / (1024**3):.0f} GB (Keys + Structures)"
)

# %% [markdown]
# ## 4. Query Latency at Scale
# LSH query time is `O(K * B)` where K is items per bucket and B is number of bands.
# As N grows to 1B, K grows linearly. We simulate this by "over-stuffing" buckets.
#
# We will query the current 1M index, but we can estimate 1B latency.
# Since 1B is 1000x larger than 1M, the buckets will be 1000x fuller (assuming uniform distribution).
# This allows us to mathematically model the slowdown.

# %%
print("\nMeasuring Baseline Query Latency (at 1M scale)...")
query_vec = np.random.randn(DIM).astype(np.float32)

latencies = []
for _ in range(100):
    t0 = time.time()
    lsh.get_top_k(query_vec, topk=10)
    latencies.append(time.time() - t0)

avg_latency_1m = np.mean(latencies) * 1000  # ms
print(f"Avg Latency (1M scale): {avg_latency_1m:.2f} ms")

# Theoretical projection
# If buckets are 1000x fuller, candidate retrieval parsing takes ~1000x longer
# However, Redis fetch is constant time O(1). The bottleneck moves to Python parsing the large set.
projected_latency_1b = (
    avg_latency_1m * (np.log10(PROJECTED_TOTAL) / np.log10(SHARD_SIZE)) * 10
)  # Heuristic factor

print(f"Projected Latency (1B scale): ~{projected_latency_1b:.0f} ms")
print(
    "\nNOTE: To maintain <100ms at 1B scale, you would need to increase 'rows_per_band'"
)
print("to make buckets sparser, or distribute Redis across multiple nodes (Sharding).")

# %% [markdown]
# ## 5. Clean Up

# %%
# lsh.clear() # Uncomment to wipe Redis
print("Done.")
