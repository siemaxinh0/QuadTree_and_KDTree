from kdtree import *

from QuadTree.algorithmsVis import load_points_csv, load_query_rect

def run_test():
    points = load_points_csv("../output/custom/custom_1.csv")

    # pts = [Point(1, 2), Point(5, 5), Point(8, 1), Point(2, 9)]
    tree = KDTree(points)

    # Szukamy punktów w obszarze środka (3,3) o połowie szerokości/wysokości 2
    area = load_query_rect("../output/custom/custom_1.query.csv")
    found = tree.query_range(area)

    tree = KDTree(points)
    for p in found:
        print(f" - Punkt: ({p.x}, {p.y})")

if __name__ == "__main__":
    run_test()