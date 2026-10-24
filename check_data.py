from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import load_iris, load_wine


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
IRIS_FEATURE_COLUMNS = [
    "sepal length (cm)",
    "sepal width (cm)",
    "petal length (cm)",
    "petal width (cm)",
    "target",
]
IRIS_DERIVED_COLUMNS = ["sepal_area", "petal_area"]
WINE_COLUMNS = list(load_wine(as_frame=True).frame.columns)
EXPECTED_FILES = {
    "base": {"iris.csv"},
    "wine": {"iris.csv", "wine.csv"},
    "iris_features": {"iris.csv"},
    "merged": {"iris.csv", "wine.csv"},
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate(state: str) -> list[dict[str, object]]:
    if not DATA_DIR.is_dir():
        raise ValueError("Missing expected directory: data")

    csv_paths = sorted(DATA_DIR.glob("*.csv"))
    actual_files = {path.name for path in csv_paths}
    if actual_files != EXPECTED_FILES[state]:
        raise ValueError(
            f"Unexpected CSV files for {state}: expected {sorted(EXPECTED_FILES[state])}, "
            f"found {sorted(actual_files)}"
        )

    iris_path = DATA_DIR / "iris.csv"
    if not iris_path.is_file():
        raise ValueError("Missing expected file: data/iris.csv")
    iris = pd.read_csv(iris_path)
    if any(re.match(r"^Unnamed:", column) for column in iris.columns):
        raise ValueError("data/iris.csv contains an unnamed index column")
    if len(iris) != 150:
        raise ValueError(f"data/iris.csv has {len(iris)} rows; expected 150")

    feature_state = state in {"iris_features", "merged"}
    expected_iris_columns = IRIS_FEATURE_COLUMNS + (IRIS_DERIVED_COLUMNS if feature_state else [])
    if list(iris.columns) != expected_iris_columns:
        raise ValueError(
            f"Unexpected Iris columns: expected {expected_iris_columns}, found {list(iris.columns)}"
        )

    source_iris = load_iris(as_frame=True).frame
    actual_source = iris[IRIS_FEATURE_COLUMNS].sort_values(
        IRIS_FEATURE_COLUMNS, kind="mergesort"
    ).reset_index(drop=True)
    expected_source = source_iris.sort_values(
        IRIS_FEATURE_COLUMNS, kind="mergesort"
    ).reset_index(drop=True)
    if not actual_source.equals(expected_source):
        raise ValueError("Iris source features or target differ from scikit-learn")

    if feature_state:
        expected_sepal_area = iris["sepal length (cm)"] * iris["sepal width (cm)"]
        expected_petal_area = iris["petal length (cm)"] * iris["petal width (cm)"]
        if not np.allclose(iris["sepal_area"], expected_sepal_area, rtol=1e-9, atol=1e-10):
            raise ValueError("sepal_area contains incorrect values")
        if not np.allclose(iris["petal_area"], expected_petal_area, rtol=1e-9, atol=1e-10):
            raise ValueError("petal_area contains incorrect values")

    if "wine.csv" in actual_files:
        wine_path = DATA_DIR / "wine.csv"
        wine = pd.read_csv(wine_path)
        if any(re.match(r"^Unnamed:", column) for column in wine.columns):
            raise ValueError("data/wine.csv contains an unnamed index column")
        if len(wine) != 178:
            raise ValueError(f"data/wine.csv has {len(wine)} rows; expected 178")
        if list(wine.columns) != WINE_COLUMNS:
            raise ValueError(f"Unexpected Wine columns: expected {WINE_COLUMNS}, found {list(wine.columns)}")
        expected_wine = load_wine(as_frame=True).frame.sort_values(
            WINE_COLUMNS, kind="mergesort"
        ).reset_index(drop=True)
        if not all(
            np.allclose(wine[column], expected_wine[column], rtol=1e-9, atol=1e-10)
            for column in WINE_COLUMNS
        ):
            raise ValueError("Wine values differ from scikit-learn")

    reports: list[dict[str, object]] = []
    for path in csv_paths:
        frame = pd.read_csv(path)
        reports.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": sha256_file(path),
                "rows": len(frame),
                "columns_count": len(frame.columns),
                "columns": list(frame.columns),
                "missing_values": int(frame.isna().sum().sum()),
            }
        )
    return reports


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate prepared Iris and Wine CSV files.")
    parser.add_argument("--state", choices=tuple(EXPECTED_FILES), required=True)
    arguments = parser.parse_args()
    try:
        print(json.dumps(validate(arguments.state), ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError) as error:
        print(f"Data validation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()