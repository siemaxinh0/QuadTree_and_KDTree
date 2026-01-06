import csv


def load_points_csv(path: str):
    pts = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r, None)  # header: x,y
        for row in r:
            pts.append(QTPoint(float(row[0]), float(row[1])))
    return pts


def load_query_rect(query_csv_path: str) -> Rect:
    with open(query_csv_path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r, None)              # header
        cx, cy, hw, hh = next(r)   # jedna linia
    return Rect(cx=float(cx), cy=float(cy), hw=float(hw), hh=float(hh))
