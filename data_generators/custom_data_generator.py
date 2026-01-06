# custom_data_generator.py
import os
import csv

import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector

from quadtree import Rect


def _save_csv(points, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["x", "y"])
        w.writerows(points)


# >>> DODANE: zapis prostokąta query do pliku <<<
def _save_query_rect(r: Rect, filepath: str):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cx", "cy", "hw", "hh"])
        w.writerow([r.cx, r.cy, r.hw, r.hh])


def _rect_from_corners(x0, y0, x1, y1):
    xmin, xmax = (x0, x1) if x0 <= x1 else (x1, x0)
    ymin, ymax = (y0, y1) if y0 <= y1 else (y1, y0)
    cx = (xmin + xmax) / 2.0
    cy = (ymin + ymax) / 2.0
    hw = (xmax - xmin) / 2.0
    hh = (ymax - ymin) / 2.0
    return Rect(cx=cx, cy=cy, hw=hw, hh=hh)


def make_custom_points_and_query(
    out_dir="output/custom",
    name_prefix="custom",
    title="Klikaj punkty (LPM dodaj, PPM usuń), przeciągnij prostokąt (query), Enter = koniec",
):
    points = []
    query_rect = {"rect": None}
    rect_patch = {"artist": None}

    fig, ax = plt.subplots()
    ax.set_title(title)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True)
    ax.axis("equal")

    scat = ax.scatter([], [], s=25)

    status = ax.text(
        0.02, 0.98, "",
        transform=ax.transAxes,
        va="top"
    )

    def refresh():
        if points:
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            scat.set_offsets(list(zip(xs, ys)))
        else:
            scat.set_offsets(np.empty((0, 2)))

        q = query_rect["rect"]
        if q is None:
            status.set_text(f"points={len(points)} | query=brak (zaznacz prostokąt)")
        else:
            status.set_text(f"points={len(points)} | query center=({q.cx:.2f},{q.cy:.2f}) hw={q.hw:.2f} hh={q.hh:.2f}")
        fig.canvas.draw_idle()

    def on_click(event):
        if event.inaxes != ax:
            return
        if event.xdata is None or event.ydata is None:
            return

        x, y = float(event.xdata), float(event.ydata)

        # LPM dodaj
        if event.button == 1:
            points.append((x, y))
            refresh()
            return

        # PPM usuń najbliższy
        if event.button == 3 and points:
            best_i = 0
            best_d = float("inf")
            for i, (px, py) in enumerate(points):
                d = (px - x) * (px - x) + (py - y) * (py - y)
                if d < best_d:
                    best_d = d
                    best_i = i
            points.pop(best_i)
            refresh()
            return

    def on_select(eclick, erelease):
        if eclick.xdata is None or eclick.ydata is None or erelease.xdata is None or erelease.ydata is None:
            return

        r = _rect_from_corners(eclick.xdata, eclick.ydata, erelease.xdata, erelease.ydata)
        query_rect["rect"] = r

        if rect_patch["artist"] is not None:
            rect_patch["artist"].remove()

        left = r.cx - r.hw
        right = r.cx + r.hw
        bottom = r.cy - r.hh
        top = r.cy + r.hh

        rect_patch["artist"], = ax.plot(
            [left, right, right, left, left],
            [bottom, bottom, top, top, bottom],
            linewidth=2
        )

        refresh()

    def on_key(event):
        if event.key == "enter":
            plt.close(fig)
            return
        if event.key == "c":
            points.clear()
            refresh()
            return
        if event.key == "r":
            query_rect["rect"] = None
            if rect_patch["artist"] is not None:
                rect_patch["artist"].remove()
                rect_patch["artist"] = None
            refresh()
            return

    rs = RectangleSelector(
        ax, on_select,
        useblit=True,
        button=[1],
        interactive=True
    )

    fig.canvas.mpl_connect("button_press_event", on_click)
    fig.canvas.mpl_connect("key_press_event", on_key)

    refresh()
    plt.show()

    if not points:
        raise ValueError("Nie dodano żadnych punktów.")

    if query_rect["rect"] is None:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        pad_x = 0.05 * (xmax - xmin + 1e-9)
        pad_y = 0.05 * (ymax - ymin + 1e-9)
        query_rect["rect"] = _rect_from_corners(xmin - pad_x, ymin - pad_y, xmax + pad_x, ymax + pad_y)

    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, f"{name_prefix}.csv")
    _save_csv(points, csv_path)

    # >>> DODANE: zapis query obok punktów <<<
    query_path = os.path.join(out_dir, f"{name_prefix}.query.csv")
    _save_query_rect(query_rect["rect"], query_path)

    # jeśli chcesz zachować identyczny return jak wcześniej, zostaw 3 wartości:
    return csv_path, query_rect["rect"], points
    # (plik query zapisuje się zawsze do: output/custom/<name_prefix>.query.csv)
