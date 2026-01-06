from custom_data_generator import make_custom_points_and_query

K = 1
paths = []
queries = []

for i in range(1, K + 1):
    points_csv, query_rect, pts = make_custom_points_and_query(
        out_dir="../output/custom",
        name_prefix=f"custom_{i}"
    )
    paths.append(points_csv)
    queries.append(query_rect)

    print(f"[{i}/{K}] zapisano: {points_csv} | points={len(pts)} | "
          f"query=(cx={query_rect.cx:.2f}, cy={query_rect.cy:.2f}, hw={query_rect.hw:.2f}, hh={query_rect.hh:.2f})")
