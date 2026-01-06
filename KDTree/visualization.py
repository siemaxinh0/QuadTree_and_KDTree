import os
from collections import deque

import numpy as np

from visualizer.main import Visualizer
# Zakładamy, że masz te klasy w swoim projekcie (jak w poprzednich krokach)
from KDTree.kdtree import KDTree, Point, Rect


# ---------------- KD-Tree drawing helpers ----------------

def draw_kd_tree_structure(vis: Visualizer, node, rect: Rect, depth=0, max_levels=10):
    """
    Rysuje strukturę podziałów KD-Tree.
    W przeciwieństwie do QuadTree, tutaj rysujemy pojedyncze linie (segs).
    """
    if node is None or depth > max_levels:
        return

    axis = depth % 2
    p = node.point

    if axis == 0:  # Podział pionowy (X)
        line = [((p.x, rect.bottom), (p.x, rect.top))]
        vis.add_line_segment(line, color="black", alpha=0.3, linewidths=1)

        # Nowe obszary dla rekurencji
        left_rect = Rect(rect.left + (p.x - rect.left) / 2, rect.cy, (p.x - rect.left) / 2, rect.hh)
        right_rect = Rect(rect.right - (rect.right - p.x) / 2, rect.cy, (rect.right - p.x) / 2, rect.hh)
    else:  # Podział poziomy (Y)
        line = [((rect.left, p.y), (rect.right, p.y))]
        vis.add_line_segment(line, color="black", alpha=0.3, linewidths=1)

        left_rect = Rect(rect.cx, rect.bottom + (p.y - rect.bottom) / 2, rect.hw, (p.y - rect.bottom) / 2)
        right_rect = Rect(rect.cx, rect.top - (rect.top - p.y) / 2, rect.hw, (rect.top - p.y) / 2)

    draw_kd_tree_structure(vis, node.left, left_rect, depth + 1, max_levels)
    draw_kd_tree_structure(vis, node.right, right_rect, depth + 1, max_levels)


# ---------------- Query visualization (GIF) ----------------

def kd_query_with_visualization(node, query_rect: Rect, current_rect: Rect, vis: Visualizer,
                                depth=0, found=None, visit_color="orange"):
    if found is None:
        found = []
    if node is None:
        return found

    # 1. Sprawdź czy obszar węzła przecina się z zapytaniem
    # (W KD-Tree musimy przekazywać obszar 'current_rect' dynamicznie)
    if not current_rect.intersects(query_rect):
        return found

    # Wizualizacja odwiedzanego obszaru (podświetlenie prostokąta)
    # rect_segs = [((current_rect.left, current_rect.bottom), (current_rect.right, current_rect.bottom)), ...]
    # Używamy Twojej logiki z QuadTree:
    from __main__ import rect_segments  # jeśli helpers są w tym samym pliku
    highlight = vis.add_line_segment(rect_segments(current_rect), color=visit_color, linewidths=2)

    # 2. Sprawdź punkt w węźle
    if query_rect.contains_point(node.point):
        found.append(node.point)
        vis.add_point((node.point.x, node.point.y), color="red", s=30)

    # 3. Podział obszaru na dzieci
    axis = depth % 2
    p = node.point

    if axis == 0:  # X
        left_child_rect = Rect(current_rect.left + (p.x - current_rect.left) / 2, current_rect.cy,
                               (p.x - current_rect.left) / 2, current_rect.hh)
        right_child_rect = Rect(current_rect.right - (current_rect.right - p.x) / 2, current_rect.cy,
                                (current_rect.right - p.x) / 2, current_rect.hh)
    else:  # Y
        left_child_rect = Rect(current_rect.cx, current_rect.bottom + (p.y - current_rect.bottom) / 2,
                               current_rect.hw, (p.y - current_rect.bottom) / 2)
        right_child_rect = Rect(current_rect.cx, current_rect.top - (current_rect.top - p.y) / 2,
                                current_rect.hw, (current_rect.top - p.y) / 2)

    # Rekurencyjne przeszukiwanie
    kd_query_with_visualization(node.left, query_rect, left_child_rect, vis, depth + 1, found, visit_color)
    kd_query_with_visualization(node.right, query_rect, right_child_rect, vis, depth + 1, found, visit_color)

    vis.remove_figure(highlight)
    return found


# ======================================================================
# Główna funkcja generująca GIF
# ======================================================================

def render_kdtree_gif(points, query_rect: Rect, world_rect: Rect, out_gif="kdtree.gif"):
    vis = Visualizer()
    vis.add_grid()
    vis.axis_equal()
    vis.add_title("KD-Tree Query Visualization")

    # Rysujemy wszystkie punkty w tle
    vis.add_point([(p.x, p.y) for p in points], color="blue", s=10, alpha=0.5)

    # Budujemy drzewo
    tree = KDTree(points)

    # Rysujemy strukturę drzewa (linie podziału)
    draw_kd_tree_structure(vis, tree.root, world_rect, max_levels=6)

    # Rysujemy prostokąt zapytania
    from __main__ import add_rect
    add_rect(vis, query_rect, color="purple", linewidths=3)

    # Animacja query
    kd_query_with_visualization(tree.root, query_rect, world_rect, vis)

    vis.save_gif(out_gif, interval=200)
    print(f"Zapisano animację do {out_gif}")

pts = [Point(x, y) for x, y in zip(np.random.rand(50) * 100, np.random.rand(50) * 100)]
world = Rect(50, 50, 50, 50)  # Środek 50,50, połowy boków 50 (zakres 0-100)
query = Rect(30, 30, 15, 15)  # Prostokąt zapytania

render_kdtree_gif(pts, query, world, "moje_kdtree.gif")