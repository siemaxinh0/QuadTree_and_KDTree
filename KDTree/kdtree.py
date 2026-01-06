from dataclasses import dataclass
from typing import List, Optional


# Twoje klasy bazowe
@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class Rect:
    cx: float
    cy: float
    hw: float
    hh: float

    @property
    def left(self) -> float: return self.cx - self.hw

    @property
    def right(self) -> float: return self.cx + self.hw

    @property
    def bottom(self) -> float: return self.cy - self.hh

    @property
    def top(self) -> float: return self.cy + self.hh

    def contains_point(self, p: Point) -> bool:
        return (self.left <= p.x < self.right and
                self.bottom <= p.y < self.top)

    def intersects(self, other: "Rect") -> bool:
        return not (other.left >= self.right or
                    other.right <= self.left or
                    other.bottom >= self.top or
                    other.top <= self.bottom)


class KDNode:
    def __init__(self, point: Point, left=None, right=None):
        self.point = point
        self.left = left  # Lewe/Dolne dziecko
        self.right = right  # Prawe/Górne dziecko


class KDTree:
    def __init__(self, points: List[Point]):
        self.root = self._build(points, depth=0)

    def _build(self, points: List[Point], depth: int) -> Optional[KDNode]:
        if not points:
            return None

        # Wybór osi: 0 dla X, 1 dla Y
        axis = depth % 2

        # Sortujemy punkty według wybranej osi, aby znaleźć medianę
        if axis == 0:
            points.sort(key=lambda p: p.x)
        else:
            points.sort(key=lambda p: p.y)

        median_idx = len(points) // 2

        # Tworzymy węzeł i rekurencyjnie budujemy dzieci
        return KDNode(
            point=points[median_idx],
            left=self._build(points[:median_idx], depth + 1),
            right=self._build(points[median_idx + 1:], depth + 1)
        )

    def query_range(self, range_rect: Rect) -> List[Point]:
        """Zwraca wszystkie punkty znajdujące się wewnątrz podanego prostokąta."""
        result = []
        self._search(self.root, range_rect, 0, result)
        return result

    def _search(self, node: KDNode, range_rect: Rect, depth: int, result: List[Point]):
        if node is None:
            return

        # 1. Sprawdź, czy punkt w bieżącym węźle mieści się w prostokącie
        if range_rect.contains_point(node.point):
            result.append(node.point)

        # 2. Rozstrzygnij, do których dzieci warto zajrzeć
        axis = depth % 2

        # Wartości porównawcze: współrzędna punktu i granice prostokąta
        if axis == 0:  # Oś X
            val = node.point.x
            low = range_rect.left
            high = range_rect.right
        else:  # Oś Y
            val = node.point.y
            low = range_rect.bottom
            high = range_rect.top

        # Jeśli lewa/dolna część prostokąta jest mniejsza od mediany, przeszukaj lewe dziecko
        if low < val:
            self._search(node.left, range_rect, depth + 1, result)

        # Jeśli prawa/górna część prostokąta jest większa lub równa medianie, przeszukaj prawe dziecko
        if high >= val:
            self._search(node.right, range_rect, depth + 1, result)