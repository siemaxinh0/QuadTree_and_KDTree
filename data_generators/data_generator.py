import numpy as np
import os
import csv
import math


def _rng(seed=None):
    return np.random.default_rng(seed)


def _to_tuples(arr2d):
    return [tuple(xy) for xy in arr2d.tolist()]


def _points_on_segment(p0, p1, m, rng):
    p0 = np.asarray(p0, dtype=float)
    p1 = np.asarray(p1, dtype=float)
    t = rng.random(m)[:, None]
    return p0 + t * (p1 - p0)


def generate_uniform_points(left, right, n=10**5, seed=None):
    rng = _rng(seed)
    pts = rng.uniform(left, right, size=(n, 2))
    return _to_tuples(pts)


def generate_normal_points(mean, std, n=10**5, seed=None):
    rng = _rng(seed)
    pts = rng.normal(mean, std, size=(n, 2))
    return _to_tuples(pts)


def generate_collinear_segment_points(a, b, n=100, seed=None):
    rng = np.random.default_rng(seed)
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    t = rng.random(n)[:, None]   # 0..1
    pts = a + t * (b - a)
    return [tuple(xy) for xy in pts.tolist()]


def generate_rectangle_points(a=(-10, -10), b=(10, -10), c=(10, 10), d=(-10, 10), n=100, seed=None):
    rng = _rng(seed)

    a = np.asarray(a, float); b = np.asarray(b, float)
    c = np.asarray(c, float); d = np.asarray(d, float)

    edges = [(a, b), (b, c), (c, d), (d, a)]
    lengths = np.array([np.linalg.norm(p1 - p0) for p0, p1 in edges], dtype=float)
    probs = lengths / lengths.sum()

    counts = rng.multinomial(n, probs)

    chunks = []
    for (p0, p1), m in zip(edges, counts):
        if m > 0:
            chunks.append(_points_on_segment(p0, p1, m, rng))

    pts = np.vstack(chunks) if chunks else np.empty((0, 2), dtype=float)
    return _to_tuples(pts)


def generate_square_points(a=(0, 0), b=(10, 0), c=(10, 10), d=(0, 10), axis_n=25, diag_n=20, seed=None):
    rng = _rng(seed)

    a = np.asarray(a, float); b = np.asarray(b, float)
    c = np.asarray(c, float); d = np.asarray(d, float)

    base = np.stack([a, b, c, d], axis=0)

    side1 = _points_on_segment(a, b, axis_n, rng)
    side2 = _points_on_segment(a, d, axis_n, rng)

    diag1 = _points_on_segment(a, c, diag_n, rng)
    diag2 = _points_on_segment(d, b, diag_n, rng)

    pts = np.vstack([base, side1, side2, diag1, diag2])
    return _to_tuples(pts)


def generate_grid_points(n=100):
    xs, ys = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    pts = np.stack([xs.ravel(), ys.ravel()], axis=1).astype(float)
    return _to_tuples(pts)


def generate_clustered_points(cluster_centers, cluster_std, points_per_cluster, seed=None):
    rng = _rng(seed)
    centers = np.asarray(cluster_centers, dtype=float)
    k = centers.shape[0]

    noise = rng.normal(0.0, cluster_std, size=(k, points_per_cluster, 2))
    pts = centers[:, None, :] + noise
    pts = pts.reshape(-1, 2)
    return _to_tuples(pts)


def save_csv(points, filepath):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["x", "y"])
        w.writerows(points)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def grid_side_from_n(n):
    side = int(math.isqrt(n))
    return max(1, side)


if __name__ == "__main__":
    OUT = "../output"
    ensure_dir(OUT)

    sizes = [100,1_000, 5_000, 10_000, 50_000]

    for N in sizes:
        folder = os.path.join(OUT, f"N_{N}")
        ensure_dir(folder)

        pts = generate_uniform_points(left=-10, right=10, n=N, seed=1)
        save_csv(pts, os.path.join(folder, "uniform.csv"))

        pts = generate_normal_points(mean=0, std=3, n=N, seed=2)
        save_csv(pts, os.path.join(folder, "normal.csv"))

        pts = generate_collinear_segment_points(a=(0, 0), b=(10, 5), n=N, seed=3)
        save_csv(pts, os.path.join(folder, "collinear.csv"))

        pts = generate_rectangle_points(a=(-10, -10), b=(10, -10), c=(10, 10), d=(-10, 10), n=N, seed=4)
        save_csv(pts, os.path.join(folder, "rectangle_border.csv"))

        axis_n = max(0, (N - 4) // 4)
        diag_n = axis_n
        pts = generate_square_points(a=(0, 0), b=(10, 0), c=(10, 10), d=(0, 10),
                                     axis_n=axis_n, diag_n=diag_n, seed=5)
        save_csv(pts, os.path.join(folder, "square_axes_diags.csv"))

        side = grid_side_from_n(N)
        pts = generate_grid_points(n=side)
        save_csv(pts, os.path.join(folder, f"grid_{side}x{side}.csv"))

        k = 3
        per_cluster = N // k
        centers = [(-20, -20), (0, 15), (25, -5)]
        pts = generate_clustered_points(cluster_centers=centers, cluster_std=2.0,
                                        points_per_cluster=per_cluster, seed=6)
        save_csv(pts, os.path.join(folder, f"clusters_k{k}.csv"))

        print(f"Zapisano dane dla N={N} do: {folder}")
