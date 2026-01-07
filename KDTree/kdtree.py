from dataclasses import dataclass
from typing import List, Optional
from points_util.points_classes import *

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

        axis = depth % 2

        if axis == 0:
            points.sort(key=lambda p: p.x)
        else:
            points.sort(key=lambda p: p.y)

        median_idx = len(points) // 2

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

        if range_rect.contains_point(node.point):
            result.append(node.point)

        axis = depth % 2

        if axis == 0:  # Oś X
            val = node.point.x
            low = range_rect.left
            high = range_rect.right
        else:  # Oś Y
            val = node.point.y
            low = range_rect.bottom
            high = range_rect.top

        if low < val:
            self._search(node.left, range_rect, depth + 1, result)

        if high >= val:
            self._search(node.right, range_rect, depth + 1, result)