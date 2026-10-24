from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.datasets import load_iris, load_wine


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"


def save_frame(frame: pd.DataFrame, destination: Path) -> None:
    ordered = frame.sort_values(list(frame.columns), kind="mergesort").reset_index(drop=True)
    ordered.to_csv(destination, index=False, lineterminator="\n", float_format="%.10g")


def prepare(mode: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if mode == "base":
        save_frame(load_iris(as_frame=True).frame, DATA_DIR / "iris.csv")
        (DATA_DIR / "wine.csv").unlink(missing_ok=True)
        return

    if mode == "wine":
        save_frame(load_wine(as_frame=True).frame, DATA_DIR / "wine.csv")
        return

    iris = load_iris(as_frame=True).frame
    iris["sepal_area"] = iris["sepal length (cm)"] * iris["sepal width (cm)"]
    iris["petal_area"] = iris["petal length (cm)"] * iris["petal width (cm)"]
    save_frame(iris, DATA_DIR / "iris.csv")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a deterministic scikit-learn dataset version.")
    parser.add_argument("mode", choices=("base", "wine", "iris_features"))
    arguments = parser.parse_args()
    prepare(arguments.mode)


if __name__ == "__main__":
    main()