"""Fit a power-prediction model from a collected dataset.

Reads the JSONL produced by ``dataset.py`` (rows of device features + measured
``watts``) and fits a linear model by ordinary least squares — pure Python, no
ML dependency. The result is a ``model.json`` of intercept + per-feature
coefficients that ``powerguess`` loads via ``MODEL_FILE`` (see docs/dataset.md).

    python train.py --data powerguess.jsonl --out model.json

Train per architecture for best results — x86 RAPL and ARM SBCs behave
differently:

    python train.py --data powerguess.jsonl --arch aarch64 --out pi.json
"""

from __future__ import annotations

import argparse
import json
from typing import List, Optional

from powerguess.model import FEATURES


def _solve(ata: List[List[float]], atb: List[float]) -> List[float]:
    """Solve the normal-equation system (A^T A) x = A^T b by Gaussian elimination."""
    n = len(atb)
    m = [row[:] + [atb[i]] for i, row in enumerate(ata)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-12:
            continue  # singular column (e.g. a constant feature) -> 0 weight
        m[col], m[pivot] = m[pivot], m[col]
        piv = m[col][col]
        m[col] = [v / piv for v in m[col]]
        for r in range(n):
            if r != col and abs(m[r][col]) > 1e-12:
                factor = m[r][col]
                m[r] = [a - factor * b for a, b in zip(m[r], m[col])]
    return [m[i][n] for i in range(n)]


def fit(rows: List[dict], features: Optional[List[str]] = None) -> dict:
    """Least-squares fit of watts ~ features. Returns a model dict."""
    features = features or FEATURES
    # Design matrix with a leading 1 for the intercept.
    x = [[1.0] + [float(r.get(f, 0.0)) for f in features] for r in rows]
    y = [float(r["watts"]) for r in rows]
    cols = len(features) + 1
    ata = [[sum(x[k][i] * x[k][j] for k in range(len(x))) for j in range(cols)]
           for i in range(cols)]
    atb = [sum(x[k][i] * y[k] for k in range(len(x))) for i in range(cols)]
    beta = _solve(ata, atb)
    return {
        "intercept": round(beta[0], 6),
        "coefficients": {f: round(beta[i + 1], 6) for i, f in enumerate(features)},
        "n_samples": len(rows),
        "features": features,
    }


def _rmse(rows: List[dict], model: dict) -> float:
    feats = model["features"]
    se = 0.0
    for r in rows:
        pred = model["intercept"] + sum(model["coefficients"][f] * float(r.get(f, 0.0))
                                        for f in feats)
        se += (pred - float(r["watts"])) ** 2
    return (se / len(rows)) ** 0.5 if rows else 0.0


def load_rows(path: str, arch: Optional[str] = None) -> List[dict]:
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if arch and row.get("arch") != arch:
                continue
            if "watts" in row:
                rows.append(row)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description="Fit a powerguess model from a dataset.")
    ap.add_argument("--data", required=True, help="dataset JSONL from dataset.py")
    ap.add_argument("--out", default="model.json", help="output model JSON")
    ap.add_argument("--arch", default=None, help="only train on rows of this arch")
    args = ap.parse_args()

    rows = load_rows(args.data, arch=args.arch)
    if len(rows) < len(FEATURES) + 1:
        raise SystemExit(f"need at least {len(FEATURES) + 1} samples, got {len(rows)}")
    model = fit(rows)
    with open(args.out, "w") as f:
        json.dump(model, f, indent=2)
    print(f"fit {model['n_samples']} samples -> {args.out}  (RMSE {_rmse(rows, model):.2f} W)")


if __name__ == "__main__":
    main()
