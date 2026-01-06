from points_util.prepare_queries import prepare_queries_for_N
from points_util.time_compare import bench_both_all, save_separate_tables_both

# sizes = [100,1000,10000,100000]
# for s in sizes:
#     prepare_queries_for_N(s)

OUTPUT_ROOT = "output"
results = bench_both_all(OUTPUT_ROOT, capacity=8, max_depth=16)
paths = save_separate_tables_both(results, out_dir="times", prefer_xlsx=True)
print("Zapisano pliki:")
for p in paths:
    print(" -", p)