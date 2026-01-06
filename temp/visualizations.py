from algorithmsVis import run_for_custom, run_images_for_N, run_for_N
from quadtree import Rect
from algorithmsVis import run_images_for_N

run_for_N(
    N=100,
    capacity=8,
    max_depth=16,
    sample_points=5000,
    max_levels=10
)
# ===================================================================

# run_for_custom(custom_dir="output/custom", capacity=1, max_depth=16, sample_points=800, max_levels=10)
