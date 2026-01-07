import os
import csv
import time
import glob
import pandas as pd

from QuadTree.quadtree import bounding_rect_pairwise, QuadTree
from points_util.points_classes import Point, Rect  # WAŻNE: Rect z left/right/top/bottom
from KDTree.kdtree import KDTree

def load_xy_csv(path: str):
    pts = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r, None)
        for row in r:
            pts.append((float(row[0]), float(row[1])))
    return pts


def load_query_rect(query_csv_path: str) -> Rect:
    with open(query_csv_path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r, None)
        cx, cy, hw, hh = next(r)
    return Rect(cx=float(cx), cy=float(cy), hw=float(hw), hh=float(hh))


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


def bench_both_file(csv_path: str, query_rect: Rect, capacity=8, max_depth=16):
    xy = load_xy_csv(csv_path)
    n = len(xy)

    pts = [Point(x, y) for (x, y) in xy]  # points_util.Point

    # -------- QuadTree
    t0 = time.perf_counter()
    world = bounding_rect_pairwise(pts)
    qt = QuadTree(world, capacity=capacity, max_depth=max_depth)
    for p in pts:
        qt.insert(p)
    t1 = time.perf_counter()
    qt_build_s = t1 - t0

    t2 = time.perf_counter()
    qt_hits = qt.query(query_rect)
    t3 = time.perf_counter()
    qt_query_s = t3 - t2

    # -------- KDTree
    t4 = time.perf_counter()
    kd = KDTree(list(pts))
    t5 = time.perf_counter()
    kd_build_s = t5 - t4

    t6 = time.perf_counter()
    kd_hits = kd.query_range(query_rect)
    t7 = time.perf_counter()
    kd_query_s = t7 - t6

    return {
        "file": os.path.basename(csv_path),
        "path": csv_path,
        "n": n,
        "capacity": capacity,
        "max_depth": max_depth,

        "qt_build_s": qt_build_s,
        "qt_query_s": qt_query_s,
        "qt_hits": len(qt_hits),

        "kd_build_s": kd_build_s,
        "kd_query_s": kd_query_s,
        "kd_hits": len(kd_hits),
    }


def bench_both_all(output_root: str, capacity=8, max_depth=16):
    csv_files = sorted(glob.glob(os.path.join(output_root, "**", "*.csv"), recursive=True))
    csv_files = [p for p in csv_files if not p.endswith(".query.csv")]

    results = []
    for csv_path in csv_files:
        query_path = csv_path.replace(".csv", ".query.csv")
        if not os.path.exists(query_path):
            raise FileNotFoundError(f"Brak query: {query_path} (dla {csv_path})")

        query_rect = load_query_rect(query_path)
        r = bench_both_file(csv_path, query_rect, capacity=capacity, max_depth=max_depth)
        results.append(r)

        print(
            f"{r['path']} | "
            f"QT build={r['qt_build_s']:.4f}s query={r['qt_query_s']:.4f}s hits={r['qt_hits']} | "
            f"KD build={r['kd_build_s']:.4f}s query={r['kd_query_s']:.4f}s hits={r['kd_hits']}"
        )

    return results


def save_separate_tables_both(results, out_dir="times", prefer_xlsx=True):
    os.makedirs(out_dir, exist_ok=True)

    df = pd.DataFrame(results).copy()
    df["Dataset"] = df["file"].apply(dataset_name_from_file)

    out = df.rename(columns={
        "n": "PointsNo",

        "qt_hits": "QT_FoundPoints",
        "qt_build_s": "QuadTreeBuildTime",
        "qt_query_s": "QuadTreeQueryTime",

        "kd_hits": "KD_FoundPoints",
        "kd_build_s": "KDTreeBuildTime",
        "kd_query_s": "KDTreeQueryTime",
    })

    out = out[[
        "Dataset", "PointsNo",
        "QT_FoundPoints", "QuadTreeBuildTime", "QuadTreeQueryTime",
        "KD_FoundPoints", "KDTreeBuildTime", "KDTreeQueryTime",
    ]]

    can_xlsx = False
    if prefer_xlsx:
        try:
            import openpyxl  # noqa
            can_xlsx = True
        except Exception:
            can_xlsx = False

    saved = []
    for dataset, g in out.groupby("Dataset"):
        g = g.sort_values("PointsNo")
        safe = dataset.replace("/", "_").replace("\\", "_")

        # nadpisujemy (bez timestampu)
        if can_xlsx:
            path = os.path.join(out_dir, f"{safe}.xlsx")
            g.to_excel(path, index=False)
        else:
            path = os.path.join(out_dir, f"{safe}.csv")
            g.to_csv(path, index=False)

        saved.append(path)

    return saved


    OUTPUT_ROOT = "../output"
    results = bench_both_all(OUTPUT_ROOT, capacity=8, max_depth=16)
    paths = save_separate_tables_both(results, out_dir="times", prefer_xlsx=True)

    print("Zapisano pliki:")
    for p in paths:
        print(" -", p)
