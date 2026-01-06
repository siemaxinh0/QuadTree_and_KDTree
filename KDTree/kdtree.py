import operator


# klasa reprezentująca pojedynczy węzeł w drzewie
class Node:
    def __init__(self, point, left=None, right=None):
        self.point = point
        self.left = left
        self.right = right


# funkcja budująca drzewo k-d z listy punktów
def build_kdtree(points, depth=0):
    # warunek stopu rekurencji, jeśli lista punktów jest pusta
    if not points:
        return None

    # wymiar przestrzeni to 2 (x, y)
    k = 2

    # obliczamy oś podziału: 0 dla x, 1 dla y
    axis = depth % k

    # sortujemy punkty względem aktualnej osi, aby znaleźć medianę
    points.sort(key=operator.itemgetter(axis))

    # znajdujemy indeks środkowy
    median = len(points) // 2

    # tworzymy węzeł z punktu środkowego i rekurencyjnie budujemy poddrzewa
    return Node(
        point=points[median],
        left=build_kdtree(points[:median], depth + 1),
        right=build_kdtree(points[median + 1:], depth + 1)
    )


# funkcja wyszukująca punkty w zadanym prostokącie [x1, x2] x [y1, y2]
def range_search(node, x1, x2, y1, y2, depth=0, results=None):
    # inicjalizacja listy wyników przy pierwszym wywołaniu
    if results is None:
        results = []

    # jeśli węzeł jest pusty, wracamy
    if node is None:
        return results

    # rozpakowujemy współrzędne punktu w aktualnym węźle
    px, py = node.point

    # wymiar przestrzeni to 2
    k = 2

    # określamy, która oś była użyta do podziału na tym poziomie
    axis = depth % k

    # sprawdzamy, czy punkt z węzła mieści się w zadanym prostokącie
    # warunek z obrazka: x1 <= qx <= x2 oraz y1 <= qy <= y2
    if x1 <= px <= x2 and y1 <= py <= y2:
        results.append(node.point)

    # decydujemy, czy przeszukiwać lewe poddrzewo
    # logika odcinania gałęzi (pruning) dla optymalizacji
    if axis == 0:
        # jeśli dzielimy po x, sprawdzamy lewą stronę tylko gdy punkt węzła >= x1
        if px >= x1:
            range_search(node.left, x1, x2, y1, y2, depth + 1, results)
    else:
        # jeśli dzielimy po y, sprawdzamy lewą stronę tylko gdy punkt węzła >= y1
        if py >= y1:
            range_search(node.left, x1, x2, y1, y2, depth + 1, results)

    # decydujemy, czy przeszukiwać prawe poddrzewo
    if axis == 0:
        # jeśli dzielimy po x, sprawdzamy prawą stronę tylko gdy punkt węzła <= x2
        if px <= x2:
            range_search(node.right, x1, x2, y1, y2, depth + 1, results)
    else:
        # jeśli dzielimy po y, sprawdzamy prawą stronę tylko gdy punkt węzła <= y2
        if py <= y2:
            range_search(node.right, x1, x2, y1, y2, depth + 1, results)

    return results


# --- testowanie rozwiązania ---

# przykładowy zbiór punktów P
points = [(2, 3), (5, 4), (9, 6), (4, 7), (8, 1), (7, 2)]

# budujemy drzewo
tree = build_kdtree(points)

# definicja zakresu z obrazka
x1, x2 = 3, 8
y1, y2 = 2, 5

# wykonujemy zapytanie
found_points = range_search(tree, x1, x2, y1, y2)

print(f"Punkty w zbiorze P: {points}")
print(f"Zakres szukania: x[{x1}, {x2}], y[{y1}, {y2}]")
print(f"Znalezione punkty q: {found_points}")