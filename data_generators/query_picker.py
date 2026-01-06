# query_picker.py
import os
import csv
import glob

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

from QuadTree.quadtree import Rect


def load_points_csv_xy(path: str):
    pts = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r, None)  # header
        for row in r:
            pts.append((float(row[0]), float(row[1])))
    return pts


def save_query_rect(r: Rect, query_path: str):
    with open(query_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cx", "cy", "hw", "hh"])
        w.writerow([r.cx, r.cy, r.hw, r.hh])


def rect_from_corners(x0, y0, x1, y1) -> Rect:
    xmin, xmax = (x0, x1) if x0 <= x1 else (x1, x0)
    ymin, ymax = (y0, y1) if y0 <= y1 else (y1, y0)
    cx = (xmin + xmax) / 2.0
    cy = (ymin + ymax) / 2.0
    hw = (xmax - xmin) / 2.0
    hh = (ymax - ymin) / 2.0
    return Rect(cx=cx, cy=cy, hw=hw, hh=hh)


def pick_query_for_existing_csv(points_csv_path: str, sample_points=5000):
    pts = load_points_csv_xy(points_csv_path)

    if sample_points is not None and len(pts) > sample_points:
        step = max(1, len(pts) // sample_points)
        pts_vis = pts[::step]
    else:
        pts_vis = pts

    query_rect = {"rect": None}
    rect_artist = {"artist": None}
    drag = {"active": False, "x0": None, "y0": None, "xlim": None, "ylim": None}

    fig, ax = plt.subplots()
    ax.set_title(f"QUERY: PPM+drag zaznacz | Enter = zapisz\n{os.path.basename(points_csv_path)}")
    ax.grid(True)
    ax.axis("equal")

    ax.scatter([p[0] for p in pts_vis], [p[1] for p in pts_vis], s=8, alpha=0.6)

    status = ax.text(0.02, 0.98, "query=brak (PPM+drag)", transform=ax.transAxes, va="top")

    def set_rect_artist(x0, y0, x1, y1):
        xmin, xmax = (x0, x1) if x0 <= x1 else (x1, x0)
        ymin, ymax = (y0, y1) if y0 <= y1 else (y1, y0)
        xs = [xmin, xmax, xmax, xmin, xmin]
        ys = [ymin, ymin, ymax, ymax, ymin]
        if rect_artist["artist"] is None:
            (rect_artist["artist"],) = ax.plot(xs, ys, linewidth=2)
        else:
            rect_artist["artist"].set_data(xs, ys)

    def on_press(event):
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            return
        if event.button != 3:  # PPM
            return

        drag["active"] = True
        drag["x0"], drag["y0"] = float(event.xdata), float(event.ydata)
        drag["xlim"] = ax.get_xlim()
        drag["ylim"] = ax.get_ylim()

        set_rect_artist(drag["x0"], drag["y0"], drag["x0"], drag["y0"])
        fig.canvas.draw_idle()

    def on_motion(event):
        if not drag["active"]:
            return
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            return

        x1, y1 = float(event.xdata), float(event.ydata)
        set_rect_artist(drag["x0"], drag["y0"], x1, y1)

        # nie pozwól matplotlibowi zmieniać skali przez rysowanie prostokąta
        ax.set_xlim(*drag["xlim"])
        ax.set_ylim(*drag["ylim"])
        fig.canvas.draw_idle()

    def on_release(event):
        if event.button != 3:
            return
        if not drag["active"]:
            return
        drag["active"] = False

        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            return

        x1, y1 = float(event.xdata), float(event.ydata)
        r = rect_from_corners(drag["x0"], drag["y0"], x1, y1)
        query_rect["rect"] = r

        status.set_text(f"query: cx={r.cx:.2f}, cy={r.cy:.2f}, hw={r.hw:.2f}, hh={r.hh:.2f}")
        ax.set_xlim(*drag["xlim"])
        ax.set_ylim(*drag["ylim"])
        fig.canvas.draw_idle()

    def on_key(event):
        if event.key == "enter":
            plt.close(fig)

    fig.canvas.mpl_connect("button_press_event", on_press)
    fig.canvas.mpl_connect("motion_notify_event", on_motion)
    fig.canvas.mpl_connect("button_release_event", on_release)
    fig.canvas.mpl_connect("key_press_event", on_key)

    plt.show()

    if query_rect["rect"] is None:
        raise ValueError("Nie zaznaczono query (PPM+drag).")

    query_path = points_csv_path.replace(".csv", ".query.csv")
    save_query_rect(query_rect["rect"], query_path)
    return query_path, query_rect["rect"]



def pick_queries_in_folder(folder: str, sample_points=5000):
    csv_files = sorted(glob.glob(os.path.join(folder, "*.csv")))
    csv_files = [p for p in csv_files if not p.endswith(".query.csv")]

    if not csv_files:
        raise FileNotFoundError(f"Brak CSV w folderze: {folder}")

    for p in csv_files:
        query_path, _ = pick_query_for_existing_csv(p, sample_points=sample_points)
        print(f"Zapisano query: {query_path}")
