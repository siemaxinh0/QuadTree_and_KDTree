import os
import csv
import time
import glob
import pandas as pd
from quadtree import Rect, QuadTree, bounding_rect_pairwise, Point


def load_xy_csv(path):
    pts = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r, None)  # nagłówek
        for row in r:
            pts.append((float(row[0]), float(row[1])))
    return pts


def build_quadtree_from_xy(xy, capacity=8, max_depth=16):
    points = [Point(x, y) for (x, y) in xy]
    world = bounding_rect_pairwise(points)
    qt = QuadTree(world, capacity=capacity, max_depth=max_depth)
    for p in points:
        qt.insert(p)
    return qt


def bench_quadtree_file(csv_path, query_square: Rect, capacity=8, max_depth=16):
    xy = load_xy_csv(csv_path)
    n = len(xy)

    # build time
    t0 = time.perf_counter()
    qt = build_quadtree_from_xy(xy, capacity=capacity, max_depth=max_depth)
    t1 = time.perf_counter()
    build_s = t1 - t0

    # ONE query time
    t2 = time.perf_counter()
    hits = qt.query(query_square)
    t3 = time.perf_counter()
    query_s = t3 - t2

    return {
        "file": os.path.basename(csv_path),
        "path": csv_path,
        "n": n,
        "capacity": capacity,
        "max_depth": max_depth,
        "build_s": build_s,
        "query_s": query_s,
        "hits": len(hits),
    }


def bench_quadtree_all(output_root, query_square: Rect, capacity=8, max_depth=16):
    csv_files = sorted(glob.glob(os.path.join(output_root, "**", "*.csv"), recursive=True))

    results = []
    for path in csv_files:
        if os.path.basename(path).startswith("bench_"):
            continue

        r = bench_quadtree_file(path, query_square, capacity=capacity, max_depth=max_depth)
        results.append(r)

        print(f"{r['path']} | build={r['build_s']:.4f}s | query={r['query_s']:.4f}s | hits={r['hits']}")

    return results


def save_separate_tables(results, out_dir="times"):
    os.makedirs(out_dir, exist_ok=True)

    # DataFrame z wyników
    df = pd.DataFrame(results).copy()

    df["Dataset"] = df["file"].apply(dataset_name_from_file)

    df_out = df.rename(columns={
        "n": "PointsNo",
        "hits": "FoundPoints",
        "build_s": "QuadTreeBuildTime",
        "query_s": "QuadTreeQueryTime",
    })

    df_out = df_out[["Dataset", "PointsNo", "FoundPoints", "QuadTreeBuildTime", "QuadTreeQueryTime"]]

    try:
        import openpyxl
        can_xlsx = True
    except ImportError:
        can_xlsx = False

    ts = time.strftime("%Y%m%d_%H%M%S")
    saved = []

    for dataset, g in df_out.groupby("Dataset"):
        g = g.sort_values("PointsNo")

        safe = dataset.replace("/", "_").replace("\\", "_")

        if can_xlsx:
            path = os.path.join(out_dir, f"{safe}_{ts}.xlsx")
            g.to_excel(path, index=False)
        else:
            path = os.path.join(out_dir, f"{safe}_{ts}.csv")
            g.to_csv(path, index=False)

        saved.append(path)

    return saved

def dataset_name_from_file(filename: str) -> str:
    base = os.path.splitext(filename)[0].lower()

    if base.startswith("grid"):
        return "siatka"
    if base.startswith("clusters"):
        return "klastry"

    mapping = {
        "normal": "rozkład normalny",
        "uniform": "rozkład jednostajny",
        "collinear": "współliniowe",
        "rectangle_border": "obwód prostokąta",
        "square_axes_diags": "kwadrat (boki+przekątne)",
    }
    return mapping.get(base, base)
