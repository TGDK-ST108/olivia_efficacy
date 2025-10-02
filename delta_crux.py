#!/usr/bin/env python3
import math
import hashlib
from typing import List, Dict

# ---------- SINGLE FOLD ----------
def delta_crux_scalar(values: List[float], crux_index: int = None) -> Dict[str, object]:
    if not values:
        raise ValueError("Values list cannot be empty.")

    n = len(values)
    if crux_index is None:
        crux_index = n // 2  # midpoint

    if not (0 <= crux_index < n):
        raise IndexError("crux_index out of range.")

    crux_value = values[crux_index]

    # deltas around pivot
    deltas = [v - crux_value for i, v in enumerate(values) if i != crux_index]
    avg_delta = sum(deltas) / len(deltas) if deltas else 0.0

    # normalized scalar
    scalar = avg_delta / (abs(crux_value) if crux_value != 0 else 1.0)

    # pact-token (sealed SHA256)
    raw = f"{values}|crux={crux_value}|scalar={scalar:.6f}"
    pact_token = hashlib.sha256(raw.encode()).hexdigest()

    return {
        "crux_value": crux_value,
        "avg_delta": avg_delta,
        "scalar": scalar,
        "pact_token": pact_token
    }

# ---------- 10-FOLD SYSTEM ----------
def delta_crux_met144(values: List[float]) -> Dict[str, object]:
    """
    Apply 10-fold Delta Crux encryption method.
    - Splits into 10 folds of equal size (padding with zeros if needed).
    - Computes Delta Crux Scalar + pact per fold.
    - Generates master seal by hashing all pact tokens together.
    """
    folds = []
    n = len(values)
    fold_size = math.ceil(n / 10)

    # create 10 folds
    for i in range(10):
        start = i * fold_size
        end = start + fold_size
        fold_vals = values[start:end]

        # pad if empty
        if not fold_vals:
            fold_vals = [0.0]

        fold_result = delta_crux_scalar(fold_vals)
        folds.append(fold_result)

    # combine pact tokens for master seal
    combined_tokens = "|".join(f["pact_token"] for f in folds)
    master_seal = hashlib.sha256(combined_tokens.encode()).hexdigest()

    return {
        "folds": folds,
        "master_seal": master_seal
    }

# ---------- EXAMPLE ----------
if __name__ == "__main__":
    data = [5, 7, 9, 11, 15, 20, 25, 33, 41, 55, 72, 91, 101]
    result = delta_crux_met144(data)

    print("10-Fold Delta Crux Scalar (met144) Result:")
    for i, fold in enumerate(result["folds"], start=1):
        print(f"  Fold {i}: scalar={fold['scalar']:.6f}, pact={fold['pact_token'][:12]}...")
    print("\nMaster Seal:", result["master_seal"])