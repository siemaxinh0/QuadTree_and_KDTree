import os
import glob

from data_generators.query_picker import pick_query_for_existing_csv


def prepare_queries_for_N(N: int, sample_points=5000, overwrite=True):
    """
    Dla każdego pliku output/N_<N>/*.csv robi (albo nadpisuje) *.query.csv
    """
    folder = os.path.join("output", f"N_{N}")
    csv_files = sorted(glob.glob(os.path.join(folder, "*.csv")))
    csv_files = [p for p in csv_files if not p.endswith(".query.csv")]

    if not csv_files:
        raise FileNotFoundError(f"Brak CSV w: {folder}")

    for csv_path in csv_files:
        query_path = csv_path.replace(".csv", ".query.csv")
        if (not overwrite) and os.path.exists(query_path):
            print(f"[SKIP] query już jest: {query_path}")
            continue

        pick_query_for_existing_csv(csv_path, sample_points=sample_points)
        print(f"[OK] zapisano query: {query_path}")


def prepare_queries_for_custom(custom_dir="output/custom", sample_points=5000, overwrite=True):
    """
    Dla każdego pliku output/custom/*.csv robi (albo nadpisuje) *.query.csv
    """
    csv_files = sorted(glob.glob(os.path.join(custom_dir, "*.csv")))
    csv_files = [p for p in csv_files if not p.endswith(".query.csv")]

    if not csv_files:
        raise FileNotFoundError(f"Brak CSV w: {custom_dir}")

    for csv_path in csv_files:
        query_path = csv_path.replace(".csv", ".query.csv")
        if (not overwrite) and os.path.exists(query_path):
            print(f"[SKIP] query już jest: {query_path}")
            continue

        pick_query_for_existing_csv(csv_path, sample_points=sample_points)
        print(f"[OK] zapisano query: {query_path}")
