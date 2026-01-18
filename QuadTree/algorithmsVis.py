import os
import glob
from collections import deque
from data_generators.query_picker import pick_query_for_existing_csv
from points_util.points_loaders import load_points_csv,load_query_rect
from visualizer.main import Visualizer
from QuadTree.quadtree import Rect, QuadTree, Point as QTPoint, bounding_rect_pairwise
import pickle
from pathlib import Path

CACHE_DIR = Path("cache_quadtree_vis")

def load_cached_quadtree(cache_path: Path):
    with cache_path.open("rb") as f:
        return pickle.load(f)

def save_cached_quadtree(tree, cache_path: Path):
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("wb") as f:
        pickle.dump(tree, f, protocol=pickle.HIGHEST_PROTOCOL)

def rect_segments(r: Rect):
    left = r.cx - r.hw
    right = r.cx + r.hw
    bottom = r.cy - r.hh
    top = r.cy + r.hh
    return [
        ((left, bottom), (right, bottom)),
        ((right, bottom), (right, top)),
        ((right, top), (left, top)),
        ((left, top), (left, bottom)),
    ]


def add_rect(vis: Visualizer, r: Rect, **kwargs):
    return vis.add_line_segment(rect_segments(r), **kwargs)



def rect_intersects(a: Rect, b: Rect) -> bool:
    if hasattr(a, "intersects"):
        return a.intersects(b)

    a_left, a_right = a.cx - a.hw, a.cx + a.hw
    a_bot, a_top = a.cy - a.hh, a.cy + a.hh
    b_left, b_right = b.cx - b.hw, b.cx + b.hw
    b_bot, b_top = b.cy - b.hh, b.cy + b.hh
    return not (b_left >= a_right or b_right <= a_left or b_bot >= a_top or b_top <= a_bot)


def rect_contains_point(r: Rect, p: QTPoint) -> bool:
    if hasattr(r, "contains_point"):
        return r.contains_point(p)

    left, right = r.cx - r.hw, r.cx + r.hw
    bottom, top = r.cy - r.hh, r.cy + r.hh
    return (left <= p.x < right) and (bottom <= p.y < top)



def draw_tree_by_levels(vis: Visualizer, root: QuadTree, max_levels=10,
                        color="black", alpha=0.25, linewidths=1):
    q = deque([(root, 0)])
    current_level = 0
    rects_this_level = []

    while q:
        node, lvl = q.popleft()
        if max_levels is not None and lvl > max_levels:
            continue

        if lvl != current_level:
            segs = []
            for r in rects_this_level:
                segs.extend(rect_segments(r))
            if segs:
                vis.add_line_segment(segs, color=color, alpha=alpha, linewidths=linewidths)
            rects_this_level = []
            current_level = lvl

        rects_this_level.append(node.boundary)

        if getattr(node, "divided", False):
            for child in (node.nw, node.ne, node.sw, node.se):
                if child is not None:
                    q.append((child, lvl + 1))

    segs = []
    for r in rects_this_level:
        segs.extend(rect_segments(r))
    if segs:
        vis.add_line_segment(segs, color=color, alpha=alpha, linewidths=linewidths)



def query_with_visualization(node: QuadTree, query_rect: Rect, vis: Visualizer,
                             found=None,
                             visit_color="orange",
                             prune_color=None,
                             found_point_color="red",
                             linewidths=2):
    if found is None:
        found = []

    if not rect_intersects(node.boundary, query_rect):
        if prune_color is not None:
            tmp = add_rect(vis, node.boundary, color=prune_color, linewidths=1, alpha=0.2)
            vis.remove_figure(tmp)
        return found

    highlight = add_rect(vis, node.boundary, color=visit_color, linewidths=linewidths, alpha=0.9)

    if not getattr(node, "divided", False):  # liść
        for p in getattr(node, "points", []):
            if rect_contains_point(query_rect, p):
                found.append(p)
                vis.add_point((p.x, p.y), color=found_point_color, s=25)
        vis.remove_figure(highlight)
        return found

    for child in (node.nw, node.ne, node.sw, node.se):
        if child is not None:
            query_with_visualization(child, query_rect, vis, found,
                                     visit_color=visit_color,
                                     prune_color=prune_color,
                                     found_point_color=found_point_color,
                                     linewidths=linewidths)

    vis.remove_figure(highlight)
    return found



def render_quadtree_image_from_csv(
    csv_path: str,
    query_square: Rect,
    capacity=8,
    max_depth=16,
    out_png="quadtree.png",
    sample_points=5000,
    max_levels=10,
):
    points = load_points_csv(csv_path)

    csv_p = Path(csv_path)
    cache_path = CACHE_DIR / f"{csv_p.stem}_cap{capacity}_d{max_depth}.pkl"

    used_cache = cache_path.exists() and cache_path.stat().st_mtime >= csv_p.stat().st_mtime
    print(f"[QT][IMAGE] {'CACHE' if used_cache else 'BUILD'} | {csv_p.name} | {cache_path.resolve()}")

    if used_cache:
        qt = load_cached_quadtree(cache_path)
        world = qt.boundary
    else:
        world = bounding_rect_pairwise(points)
        qt = QuadTree(world, capacity=capacity, max_depth=max_depth)
        for p in points:
            qt.insert(p)
        save_cached_quadtree(qt, cache_path)

    vis = Visualizer()
    vis.add_grid()
    vis.axis_equal()
    vis.add_title(f"Quadtree (image): {os.path.basename(csv_path)} [{'CACHE' if used_cache else 'BUILD'}]")

    if sample_points is not None and len(points) > sample_points:
        step = max(1, len(points) // sample_points)
        pts_vis = points[::step]
    else:
        pts_vis = points
    vis.add_point([(p.x, p.y) for p in pts_vis], color="blue", s=8, alpha=0.6)

    add_rect(vis, world, color="black", linewidths=2)
    draw_tree_by_levels(vis, qt, max_levels=max_levels, color="black", alpha=0.25, linewidths=1)

    add_rect(vis, query_square, color="purple", linewidths=2)

    found = []
    stack = [qt]
    while stack:
        node = stack.pop()
        if node is None:
            continue
        if not rect_intersects(node.boundary, query_square):
            continue
        if not getattr(node, "divided", False):
            for p in getattr(node, "points", []):
                if rect_contains_point(query_square, p):
                    found.append(p)
        else:
            stack.extend([node.nw, node.ne, node.sw, node.se])

    if found:
        vis.add_point([(p.x, p.y) for p in found], color="red", s=25)

    vis.save(out_png)
    return found


def render_quadtree_gif_from_csv(
    csv_path: str,
    query_square: Rect,
    capacity=8,
    max_depth=16,
    out_gif="quadtree.gif",
    out_png=None,
    sample_points=2000,
    max_levels=10,
    show_pruned=False,
    interval=120
):
    points = load_points_csv(csv_path)

    csv_p = Path(csv_path)
    cache_path = CACHE_DIR / f"{csv_p.stem}_cap{capacity}_d{max_depth}.pkl"

    used_cache = cache_path.exists() and cache_path.stat().st_mtime >= csv_p.stat().st_mtime
    print(f"[QT][GIF]   {'CACHE' if used_cache else 'BUILD'} | {csv_p.name} | {cache_path.resolve()}")

    if used_cache:
        qt = load_cached_quadtree(cache_path)
        world = qt.boundary
    else:
        world = bounding_rect_pairwise(points)
        qt = QuadTree(world, capacity=capacity, max_depth=max_depth)
        for p in points:
            qt.insert(p)
        save_cached_quadtree(qt, cache_path)

    vis = Visualizer()
    vis.add_grid()
    vis.axis_equal()
    vis.add_title(f"Quadtree (gif): {os.path.basename(csv_path)} [{'CACHE' if used_cache else 'BUILD'}]")

    if sample_points is not None and len(points) > sample_points:
        step = max(1, len(points) // sample_points)
        pts_vis = points[::step]
    else:
        pts_vis = points
    vis.add_point([(p.x, p.y) for p in pts_vis], color="blue", s=8, alpha=0.6)

    add_rect(vis, world, color="black", linewidths=2)
    draw_tree_by_levels(vis, qt, max_levels=max_levels, color="black", alpha=0.25, linewidths=1)

    add_rect(vis, query_square, color="purple", linewidths=2)

    found = query_with_visualization(
        qt,
        query_square,
        vis,
        prune_color=("lightgray" if show_pruned else None),
        found_point_color="red",
        visit_color="orange"
    )

    vis.save_gif(out_gif, interval=interval)
    if out_png is not None:
        vis.save(out_png)

    return found


def run_images_for_N(
    N: int,
    capacity=8,
    max_depth=16,
    sample_points=5000,
    max_levels=10
):
    in_dir = os.path.join("../output", f"N_{N}")
    out_dir = os.path.join("times", f"N_{N}", "images")
    os.makedirs(out_dir, exist_ok=True)

    csv_files = sorted(glob.glob(os.path.join(in_dir, "*.csv")))
    csv_files = [p for p in csv_files if not p.endswith(".query.csv")]

    if not csv_files:
        raise FileNotFoundError(f"Nie znaleziono CSV w: {in_dir}")

    for csv_path in csv_files:
        base = os.path.splitext(os.path.basename(csv_path))[0]
        out_png = os.path.join(out_dir, f"{base}_quadtree.png")

        query_path, query_square = pick_query_for_existing_csv(csv_path, sample_points=sample_points)

        found = render_quadtree_image_from_csv(
            csv_path=csv_path,
            query_square=query_square,
            capacity=capacity,
            max_depth=max_depth,
            out_png=out_png,
            sample_points=sample_points,
            max_levels=max_levels
        )

        print(f"[IMG] {csv_path} | query={query_path} -> hits={len(found)} | png={out_png}")


def run_for_N(
    N: int,
    capacity=8,
    max_depth=16,
    sample_points=1500,     # do rysowania (gif i picker)
    max_levels=10,
    show_pruned=False,
    interval=120,
    also_save_png=True
):
    in_dir = os.path.join("../output", f"N_{N}")
    out_dir = os.path.join("times", f"N_{N}", "gifs")
    os.makedirs(out_dir, exist_ok=True)

    csv_files = sorted(glob.glob(os.path.join(in_dir, "*.csv")))
    csv_files = [p for p in csv_files if not p.endswith(".query.csv")]

    if not csv_files:
        raise FileNotFoundError(f"Nie znaleziono CSV w: {in_dir}")

    for csv_path in csv_files:
        base = os.path.splitext(os.path.basename(csv_path))[0]
        out_gif = os.path.join(out_dir, f"{base}_quadtree.gif")
        out_png = os.path.join(out_dir, f"{base}_quadtree.png") if also_save_png else None

        # ZAWSZE pytaj o query + zapisz obok pliku
        query_path, query_square = pick_query_for_existing_csv(csv_path, sample_points=sample_points)

        found = render_quadtree_gif_from_csv(
            csv_path=csv_path,
            query_square=query_square,
            capacity=capacity,
            max_depth=max_depth,
            out_gif=out_gif,
            out_png=out_png,
            sample_points=sample_points,
            max_levels=max_levels,
            show_pruned=show_pruned,
            interval=interval
        )

        msg = f"[GIF] {csv_path} | query={query_path} -> hits={len(found)} | gif={out_gif}"
        if out_png:
            msg += f" | png={out_png}"
        print(msg)


def run_for_custom(
    custom_dir="output/custom",
    capacity=8,
    max_depth=16,
    sample_points=1500,
    max_levels=10,
    show_pruned=False,
    interval=120,
    also_save_png=True
):
    out_dir = os.path.join("times", "custom", "gifs")
    os.makedirs(out_dir, exist_ok=True)

    csv_files = sorted(glob.glob(os.path.join(custom_dir, "*.csv")))
    csv_files = [p for p in csv_files if not p.endswith(".query.csv")]

    if not csv_files:
        raise FileNotFoundError(f"Nie znaleziono custom CSV w: {custom_dir}")

    for csv_path in csv_files:
        base = os.path.splitext(os.path.basename(csv_path))[0]
        query_path = os.path.join(custom_dir, f"{base}.query.csv")
        if not os.path.exists(query_path):
            print(f"[SKIP] brak query dla: {csv_path} (szukam: {query_path})")
            continue

        query_square = load_query_rect(query_path)

        out_gif = os.path.join(out_dir, f"{base}_quadtree.gif")
        out_png = os.path.join(out_dir, f"{base}_quadtree.png") if also_save_png else None

        found = render_quadtree_gif_from_csv(
            csv_path=csv_path,
            query_square=query_square,
            capacity=capacity,
            max_depth=max_depth,
            out_gif=out_gif,
            out_png=out_png,
            sample_points=sample_points,
            max_levels=max_levels,
            show_pruned=show_pruned,
            interval=interval
        )

        msg = f"[GIF] {csv_path} -> hits={len(found)} | gif={out_gif}"
        if out_png:
            msg += f" | png={out_png}"
        print(msg)
