
from typing import List, Optional, Iterable
from points_util.points_classes import *
class QuadTree:
    """
    Quadtree w wariancie "punkty tylko w liściach":
    - Liść: przechowuje punkty (self.points)
    - Węzeł wewnętrzny: nie przechowuje punktów, tylko ma 4 dzieci

    capacity: maks. liczba punktów w liściu zanim się podzieli
    max_depth: zabezpieczenie przed zbyt głębokim dzieleniem
    """
    def __init__(self, boundary: Rect, capacity: int = 4, max_depth: int = 16, depth: int = 0):
        self.boundary = boundary
        self.capacity = capacity
        self.max_depth = max_depth
        self.depth = depth

        self.points: List[Point] = []  # używane TYLKO gdy węzeł jest liściem
        self.divided: bool = False

        self.nw: Optional["QuadTree"] = None
        self.ne: Optional["QuadTree"] = None
        self.sw: Optional["QuadTree"] = None
        self.se: Optional["QuadTree"] = None

    def is_leaf(self) -> bool:
        return not self.divided

    def subdivide(self) -> None:
        """Tworzy 4 dzieci (NW, NE, SW, SE)."""
        cx, cy, hw, hh = self.boundary.cx, self.boundary.cy, self.boundary.hw, self.boundary.hh
        child_hw = hw / 2
        child_hh = hh / 2

        # NW: x mniejsze, y większe
        nw_rect = Rect(cx - child_hw, cy + child_hh, child_hw, child_hh)
        ne_rect = Rect(cx + child_hw, cy + child_hh, child_hw, child_hh)
        sw_rect = Rect(cx - child_hw, cy - child_hh, child_hw, child_hh)
        se_rect = Rect(cx + child_hw, cy - child_hh, child_hw, child_hh)

        self.nw = QuadTree(nw_rect, self.capacity, self.max_depth, self.depth + 1)
        self.ne = QuadTree(ne_rect, self.capacity, self.max_depth, self.depth + 1)
        self.sw = QuadTree(sw_rect, self.capacity, self.max_depth, self.depth + 1)
        self.se = QuadTree(se_rect, self.capacity, self.max_depth, self.depth + 1)

        self.divided = True

    def _child_for_point(self, p: Point) -> "QuadTree":
        """
        Zwraca dziecko, do którego należy punkt.
        Zakładamy, że self.divided == True i punkt leży w self.boundary.
        """
        if self.nw.boundary.contains_point(p):
            return self.nw
        if self.ne.boundary.contains_point(p):
            return self.ne
        if self.sw.boundary.contains_point(p):
            return self.sw
        return self.se

    def insert(self, p: Point) -> bool:
        """
        Wstawia punkt.
        Zwraca False jeśli punkt jest poza boundary (nie pasuje do tego drzewa).
        """
        if not self.boundary.contains_point(p):
            return False

        if self.is_leaf():
            if len(self.points) < self.capacity or self.depth >= self.max_depth:
                self.points.append(p)
                return True

            self.subdivide()

            old_points = self.points
            self.points = []  # węzeł przestaje przechowywać punkty

            for op in old_points:
                child = self._child_for_point(op)
                child.insert(op)

            # po przerzuceniu starych punktów wstawiamy nowy
            child = self._child_for_point(p)
            return child.insert(p)

        child = self._child_for_point(p)
        return child.insert(p)

    def query(self, range_rect: Rect, found: Optional[List[Point]] = None) -> List[Point]:
        """
        Zwraca listę punktów leżących w prostokącie range_rect.
        W stylu liście-only: punkty sprawdzamy tylko w liściach.
        """
        if found is None:
            found = []

        # Jeśli obszary się nie przecinają, nie ma sensu schodzić w dół
        if not self.boundary.intersects(range_rect):
            return found

        if self.is_leaf():
            for p in self.points:
                if range_rect.contains_point(p):
                    found.append(p)
            return found

        self.nw.query(range_rect, found)
        self.ne.query(range_rect, found)
        self.sw.query(range_rect, found)
        self.se.query(range_rect, found)
        return found

def bounding_rect_pairwise(points: Iterable[Point], padding: float = 1e-9) -> Rect:
    """
    Liczy prostokąt graniczny obejmujący wszystkie punkty,
    używając metody parami (pairwise min/max), która robi mniej porównań.
    """
    pts: List[Point] = list(points)
    if not pts:
        raise ValueError("Nie można policzyć bounding rect dla pustej listy punktów.")

    n = len(pts)

    if n == 1:
        min_x = max_x = pts[0].x
        min_y = max_y = pts[0].y
        i = 1
    elif n % 2 == 0:
        p0, p1 = pts[0], pts[1]

        if p0.x < p1.x:
            min_x, max_x = p0.x, p1.x
        else:
            min_x, max_x = p1.x, p0.x

        if p0.y < p1.y:
            min_y, max_y = p0.y, p1.y
        else:
            min_y, max_y = p1.y, p0.y

        i = 2
    else:
        min_x = max_x = pts[0].x
        min_y = max_y = pts[0].y
        i = 1

    while i + 1 < n:
        a, b = pts[i], pts[i + 1]

        if a.x < b.x:
            low_x, high_x = a.x, b.x
        else:
            low_x, high_x = b.x, a.x

        if low_x < min_x:
            min_x = low_x
        if high_x > max_x:
            max_x = high_x

        if a.y < b.y:
            low_y, high_y = a.y, b.y
        else:
            low_y, high_y = b.y, a.y

        if low_y < min_y:
            min_y = low_y
        if high_y > max_y:
            max_y = high_y

        i += 2

    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0
    hw = (max_x - min_x) / 2.0 + padding
    hh = (max_y - min_y) / 2.0 + padding

    return Rect(cx=cx, cy=cy, hw=hw, hh=hh)
