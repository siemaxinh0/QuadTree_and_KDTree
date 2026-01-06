from points_util.points_classes import Point, Rect
from kdtreeVis import run_for_custom_kdtree, run_images_for_N_kdtree, run_gifs_for_N_kdtree
from points_util.prepare_queries import prepare_queries_for_N

# run_for_custom_kdtree(
#     custom_dir="../output/custom",
#     RectClass=Rect,
#     PointClass=Point,
#     sample_points=1200,
#     max_levels=10,
#     interval=120
# )
run_gifs_for_N_kdtree(100)