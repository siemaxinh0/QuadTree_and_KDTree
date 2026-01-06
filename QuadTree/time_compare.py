from points_loader import bench_quadtree_all,save_separate_tables
from quadtree import Rect

QUERY = Rect(cx=0.0, cy=0.0, hw=5.0, hh=5.0)

results = bench_quadtree_all("output", QUERY, capacity=8, max_depth=16)

paths = save_separate_tables(results, out_dir="times")
print("Zapisano pliki:")
for p in paths:
    print(" -", p)