# benchmark.py — run this to generate proof
import time
import numpy as np
from scipy.spatial import KDTree

def naive_check(sat_positions, deb_positions):
    """O(N²) naive approach"""
    results = []
    for s in sat_positions:
        for d in deb_positions:
            dist = np.linalg.norm(s - d)
            if dist < 5.0:
                results.append(dist)
    return results

def kdtree_check(sat_positions, deb_positions):
    """O(N log N) KD-Tree approach"""
    tree = KDTree(deb_positions)
    results = []
    for s in sat_positions:
        idxs = tree.query_ball_point(s, r=5.0)
        results.extend(idxs)
    return results

# Test with realistic sizes
sat_pos = np.random.uniform(-7000, 7000, (50, 3))
deb_pos = np.random.uniform(-7000, 7000, (10000, 3))

# Naive O(N²)
t0 = time.time()
naive_check(sat_pos, deb_pos)
naive_time = time.time() - t0

# KD-Tree O(N log N)
t0 = time.time()
kdtree_check(sat_pos, deb_pos)
kdtree_time = time.time() - t0

speedup = naive_time / kdtree_time
print(f"Naive O(N²):        {naive_time*1000:.1f} ms")
print(f"KD-Tree O(N log N): {kdtree_time*1000:.1f} ms")
print(f"Speedup:            {speedup:.1f}x faster")
