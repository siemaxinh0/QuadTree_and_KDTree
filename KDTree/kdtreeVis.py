# kdtreeVis.py
import os
import csv
import glob

from visualizer.main import Visualizer
from points_util.points_classes import *
from points_util.points_loaders import *



class KDNode:
    def __init__(self, point, left=None, right=None):
        self.point = point
        self.left = left
        self.right = right


class KDTree:
    def __init__(self, points):
        self.root = self._build(points, depth=0)

    def _build(self, points, depth):
        if not points:
            return None

        axis = depth % 2
        if axis == 0:
            points.sort(key=lambda p: p.x)
        else:
            points.sort(key=lambda p: p.y)

        m = len(points) // 2
        return KDNode(
            point=points[m],
            left=self._build(points[:m], depth + 1),
            right=self._build(points[m + 1:], depth + 1),
        )

    def query_range(self, range_rect):
        result = []
        _kd_search_plain(self.root, range_rect, 0, result)
        return result


def _kd_search_plain(node, range_rect, depth, result):
    if node is None:
        return
    if _rect_contains_point(range_rect, node.point):
        result.append(node.point)

    axis = depth % 2
    left, right, bottom, top = _rect_lrbt(range_rect)

    if axis == 0:
        val = node.point.x
        low, high = left, right
    else:
        val = node.point.y
        low, high = bottom, top

    if low < val:
        _kd_search_plain(node.left, range_rect, depth + 1, result)
    if high >= val:
        _kd_search_plain(node.right, range_rect, depth + 1, result)


# =========================
# HELPERY: Rect / contains
# =========================

def _rect_lrbt(r):
    # próba: Rect z .left/.right/.bottom/.top
    if all(hasattr(r, a) for a in ("left", "right", "bottom", "top")):
        return float(r.left), float(r.right), float(r.bottom), float(r.top)

    # fallback: Rect quadtree (cx,cy,hw,hh)
    left = float(r.cx - r.hw)
    right = float(r.cx + r.hw)
    bottom = float(r.cy - r.hh)
    top = float(r.cy + r.hh)
    return left, right, bottom, top


def _rect_contains_point(r, p):
    if hasattr(r, "contains_point"):
        return r.contains_point(p)
    left, right, bottom, top = _rect_lrbt(r)
    return (left <= p.x <= right) and (bottom <= p.y <= top)


def _rect_from_lrbt(left, right, bottom, top):
    # tylko do rysowania (nie musisz mieć klasy Rect)
    return (left, right, bottom, top)


def _rect_segments_lrbt(left, right, bottom, top):
    return [
        ((left, bottom), (right, bottom)),
        ((right, bottom), (right, top)),
        ((right, top), (left, top)),
        ((left, top), (left, bottom)),
    ]


def _add_rect_lrbt(vis: Visualizer, left, right, bottom, top, **kwargs):
    return vis.add_line_segment(_rect_segments_lrbt(left, right, bottom, top), **kwargs)


def _load_points_csv_as_simple_points(path: str, PointClass):
    pts = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r, None)  # header x,y
        for row in r:
            pts.append(PointClass(float(row[0]), float(row[1])))
    return pts


def _load_query_rect_csv(path: str, RectClass):
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r, None)
        cx, cy, hw, hh = next(r)
    return RectClass(cx=float(cx), cy=float(cy), hw=float(hw), hh=float(hh))


def _world_bounds(points, pad_ratio=0.05):
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    pad_x = pad_ratio * (xmax - xmin + 1e-9)
    pad_y = pad_ratio * (ymax - ymin + 1e-9)
    return xmin - pad_x, xmax + pad_x, ymin - pad_y, ymax + pad_y


# =========================
# RYSOWANIE STRUKTURY KD
# =========================

def _draw_kdtree_splits(vis: Visualizer, node, xmin, xmax, ymin, ymax, depth=0, max_levels=10,
                        color="black", alpha=0.25, linewidths=1):
    if node is None:
        return
    if max_levels is not None and depth > max_levels:
        return

    axis = depth % 2
    if axis == 0:
        x = node.point.x
        vis.add_line_segment(((x, ymin), (x, ymax)), color=color, alpha=alpha, linewidths=linewidths)
        _draw_kdtree_splits(vis, node.left, xmin, x, ymin, ymax, depth + 1, max_levels, color, alpha, linewidths)
        _draw_kdtree_splits(vis, node.right, x, xmax, ymin, ymax, depth + 1, max_levels, color, alpha, linewidths)
    else:
        y = node.point.y
        vis.add_line_segment(((xmin, y), (xmax, y)), color=color, alpha=alpha, linewidths=linewidths)
        _draw_kdtree_splits(vis, node.left, xmin, xmax, ymin, y, depth + 1, max_levels, color, alpha, linewidths)
        _draw_kdtree_splits(vis, node.right, xmin, xmax, y, ymax, depth + 1, max_levels, color, alpha, linewidths)


# =========================
# QUERY Z WIZUALIZACJĄ (GIF)
# =========================

def _kd_query_with_visualization(node, query_rect, vis: Visualizer,
                                 xmin, xmax, ymin, ymax,
                                 depth=0, found=None,
                                 visit_color="orange",
                                 found_point_color="red",
                                 prune_color=None,
                                 linewidths=2):
    if found is None:
        found = []
    if node is None:
        return found

    left, right, bottom, top = _rect_lrbt(query_rect)

    # highlight aktualnego podziału
    axis = depth % 2
    if axis == 0:
        x = node.point.x
        hi = vis.add_line_segment(((x, ymin), (x, ymax)), color=visit_color, linewidths=linewidths, alpha=0.9)
    else:
        y = node.point.y
        hi = vis.add_line_segment(((xmin, y), (xmax, y)), color=visit_color, linewidths=linewidths, alpha=0.9)

    # punkt w węźle
    if _rect_contains_point(query_rect, node.point):
        found.append(node.point)
        vis.add_point((node.point.x, node.point.y), color=found_point_color, s=25)

    # decyzja o zejściu
    if axis == 0:
        val = node.point.x
        go_left = left < val
        go_right = right >= val
        if go_left:
            _kd_query_with_visualization(node.left, query_rect, vis, xmin, val, ymin, ymax,
                                         depth + 1, found, visit_color, found_point_color, prune_color, linewidths)
        elif prune_color is not None:
            # opcjonalna wizualizacja “uciętego” obszaru
            tmp = _add_rect_lrbt(vis, xmin, val, ymin, ymax, color=prune_color, alpha=0.1, linewidths=1)
            vis.remove_figure(tmp)

        if go_right:
            _kd_query_with_visualization(node.right, query_rect, vis, val, xmax, ymin, ymax,
                                         depth + 1, found, visit_color, found_point_color, prune_color, linewidths)
        elif prune_color is not None:
            tmp = _add_rect_lrbt(vis, val, xmax, ymin, ymax, color=prune_color, alpha=0.1, linewidths=1)
            vis.remove_figure(tmp)

    else:
        val = node.point.y
        go_down = bottom < val
        go_up = top >= val

        if go_down:
            _kd_query_with_visualization(node.left, query_rect, vis, xmin, xmax, ymin, val,
                                         depth + 1, found, visit_color, found_point_color, prune_color, linewidths)
        elif prune_color is not None:
            tmp = _add_rect_lrbt(vis, xmin, xmax, ymin, val, color=prune_color, alpha=0.1, linewidths=1)
            vis.remove_figure(tmp)

        if go_up:
            _kd_query_with_visualization(node.right, query_rect, vis, xmin, xmax, val, ymax,
                                         depth + 1, found, visit_color, found_point_color, prune_color, linewidths)
        elif prune_color is not None:
            tmp = _add_rect_lrbt(vis, xmin, xmax, val, ymax, color=prune_color, alpha=0.1, linewidths=1)
            vis.remove_figure(tmp)

    vis.remove_figure(hi)
    return found


# =========================
# PUBLIC: PNG / GIF z CSV
# =========================

def render_kdtree_image_from_csv(
    csv_path: str,
    query_rect,
    PointClass,
    out_png="kdtree.png",
    sample_points=5000,
    max_levels=10,
):
    points = _load_points_csv_as_simple_points(csv_path, PointClass)
    tree = KDTree(points)

    xmin, xmax, ymin, ymax = _world_bounds(points)

    vis = Visualizer()
    vis.add_grid()
    vis.axis_equal()
    vis.add_title(f"KDTree (image): {os.path.basename(csv_path)}")

    # punkty (próbka)
    pts_vis = points
    if sample_points is not None and len(points) > sample_points:
        step = max(1, len(points) // sample_points)
        pts_vis = points[::step]
    vis.add_point([(p.x, p.y) for p in pts_vis], color="blue", s=8, alpha=0.6)

    # world + splity
    _add_rect_lrbt(vis, xmin, xmax, ymin, ymax, color="black", linewidths=2)
    _draw_kdtree_splits(vis, tree.root, xmin, xmax, ymin, ymax, depth=0, max_levels=max_levels,
                        color="black", alpha=0.25, linewidths=1)

    # query
    ql, qr, qb, qt = _rect_lrbt(query_rect)
    _add_rect_lrbt(vis, ql, qr, qb, qt, color="purple", linewidths=2)

    # wynik (bez animacji)
    found = tree.query_range(query_rect)
    if found:
        vis.add_point([(p.x, p.y) for p in found], color="red", s=25)

    vis.save(out_png)
    return found


def render_kdtree_gif_from_csv(
    csv_path: str,
    query_rect,
    PointClass,
    out_gif="kdtree.gif",
    out_png=None,
    sample_points=2000,
    max_levels=10,
    show_pruned=False,
    interval=120,
):
    points = _load_points_csv_as_simple_points(csv_path, PointClass)
    tree = KDTree(points)

    xmin, xmax, ymin, ymax = _world_bounds(points)

    vis = Visualizer()
    vis.add_grid()
    vis.axis_equal()
    vis.add_title(f"KDTree (gif): {os.path.basename(csv_path)}")

    # punkty (próbka)
    pts_vis = points
    if sample_points is not None and len(points) > sample_points:
        step = max(1, len(points) // sample_points)
        pts_vis = points[::step]
    vis.add_point([(p.x, p.y) for p in pts_vis], color="blue", s=8, alpha=0.6)

    # world + “tło” splitów
    _add_rect_lrbt(vis, xmin, xmax, ymin, ymax, color="black", linewidths=2)
    _draw_kdtree_splits(vis, tree.root, xmin, xmax, ymin, ymax, depth=0, max_levels=max_levels,
                        color="black", alpha=0.25, linewidths=1)

    # query
    ql, qr, qb, qt = _rect_lrbt(query_rect)
    _add_rect_lrbt(vis, ql, qr, qb, qt, color="purple", linewidths=2)

    found = _kd_query_with_visualization(
        tree.root, query_rect, vis,
        xmin, xmax, ymin, ymax,
        depth=0,
        prune_color=("lightgray" if show_pruned else None),
        found_point_color="red",
        visit_color="orange",
        linewidths=2
    )

    vis.save_gif(out_gif, interval=interval)
    if out_png is not None:
        vis.save(out_png)

    return found

# =========================
# RUNNERS
# =========================
def run_images_for_N_kdtree(
    N: int,
    sample_points=5000,
    max_levels=10
):
    in_dir = os.path.join("../output", f"N_{N}")
    out_dir = os.path.join("results", f"N_{N}", "images_kdtree")
    os.makedirs(out_dir, exist_ok=True)

    csv_files = sorted(glob.glob(os.path.join(in_dir, "*.csv")))
    csv_files = [p for p in csv_files if not p.endswith(".query.csv")]
    if not csv_files:
        raise FileNotFoundError(f"Nie znaleziono CSV w: {in_dir}")

    for csv_path in csv_files:
        base = os.path.splitext(os.path.basename(csv_path))[0]
        query_path = csv_path.replace(".csv", ".query.csv")

        if not os.path.exists(query_path):
            print(f"[SKIP-KD] brak query dla {csv_path} (oczekuję: {query_path})")
            continue

        query_rect = load_query_rect(query_path)
        out_png = os.path.join(out_dir, f"{base}_kdtree.png")

        found = render_kdtree_image_from_csv(
            csv_path=csv_path,
            query_rect=query_rect,
            PointClass=Point,
            out_png=out_png,
            sample_points=sample_points,
            max_levels=max_levels
        )
        print(f"[IMG-KD] {csv_path} -> hits={len(found)} | png={out_png}")


def run_gifs_for_N_kdtree(
    N: int,
    sample_points=1500,
    max_levels=10,
    show_pruned=False,
    interval=120,
    also_save_png=True
):
    in_dir = os.path.join("../output", f"N_{N}")
    out_dir = os.path.join("results", f"N_{N}", "gifs_kdtree")
    os.makedirs(out_dir, exist_ok=True)

    csv_files = sorted(glob.glob(os.path.join(in_dir, "*.csv")))
    csv_files = [p for p in csv_files if not p.endswith(".query.csv")]
    if not csv_files:
        raise FileNotFoundError(f"Nie znaleziono CSV w: {in_dir}")

    for csv_path in csv_files:
        base = os.path.splitext(os.path.basename(csv_path))[0]
        query_path = csv_path.replace(".csv", ".query.csv")

        if not os.path.exists(query_path):
            print(f"[SKIP-KD] brak query dla {csv_path} (oczekuję: {query_path})")
            continue

        query_rect = load_query_rect(query_path)

        out_gif = os.path.join(out_dir, f"{base}_kdtree.gif")
        out_png = os.path.join(out_dir, f"{base}_kdtree.png") if also_save_png else None

        found = render_kdtree_gif_from_csv(
            csv_path=csv_path,
            query_rect=query_rect,
            PointClass=Point,
            out_gif=out_gif,
            out_png=out_png,
            sample_points=sample_points,
            max_levels=max_levels,
            show_pruned=show_pruned,
            interval=interval
        )

        msg = f"[GIF-KD] {csv_path} -> hits={len(found)} | gif={out_gif}"
        if out_png:
            msg += f" | png={out_png}"
        print(msg)


# =========================
# RUNNERS (custom): output/custom/*.csv + *.query.csv
# =========================


def run_for_custom_kdtree(custom_dir, RectClass, PointClass,
                               sample_points=1500, max_levels=10,
                               show_pruned=False, interval=120, also_save_png=True):
    out_dir = os.path.join("results", "custom", "gifs_kdtree")
    os.makedirs(out_dir, exist_ok=True)

    csv_files = sorted(glob.glob(os.path.join(custom_dir, "*.csv")))
    csv_files = [p for p in csv_files if not p.endswith(".query.csv")]

    for csv_path in csv_files:
        base = os.path.splitext(os.path.basename(csv_path))[0]
        query_path = os.path.join(os.path.dirname(csv_path), f"{base}.query.csv")
        if not os.path.exists(query_path):
            print(f"[SKIP] brak query: {query_path}")
            continue

        query_rect = _load_query_rect_csv(query_path, RectClass)

        out_gif = os.path.join(out_dir, f"{base}_kdtree.gif")
        out_png = os.path.join(out_dir, f"{base}_kdtree.png") if also_save_png else None

        found = render_kdtree_gif_from_csv(
            csv_path=csv_path,
            query_rect=query_rect,
            PointClass=PointClass,
            out_gif=out_gif,
            out_png=out_png,
            sample_points=sample_points,
            max_levels=max_levels,
            show_pruned=show_pruned,
            interval=interval
        )
        msg = f"[GIF-KD] {csv_path} -> hits={len(found)} | gif={out_gif}"
        if out_png:
            msg += f" | png={out_png}"
        print(msg)
