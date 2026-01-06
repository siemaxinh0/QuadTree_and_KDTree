from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass(frozen=True)
class Rect:
    """
    Prostokąt osiowo wyrównany (AABB) w zapisie:
    - (cx, cy) = środek
    - hw, hh = połowy wymiarów (half width, half height)

    UWAGA: contains_point jest półotwarte:
    x ∈ [left, right) i y ∈ [bottom, top)
    Dzięki temu punkt na granicy trafia do dokładnie jednego dziecka.
    """
    cx: float
    cy: float
    hw: float
    hh: float

    @property
    def left(self) -> float:
        return self.cx - self.hw

    @property
    def right(self) -> float:
        return self.cx + self.hw

    @property
    def bottom(self) -> float:
        return self.cy - self.hh

    @property
    def top(self) -> float:
        return self.cy + self.hh

    def contains_point(self, p: Point) -> bool:
        return (self.left <= p.x < self.right and
                self.bottom <= p.y < self.top)

    def intersects(self, other: "Rect") -> bool:
        return not (other.left >= self.right or
                    other.right <= self.left or
                    other.bottom >= self.top or
                    other.top <= self.bottom)

