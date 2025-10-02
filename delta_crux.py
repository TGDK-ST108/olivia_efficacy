#!/usr/bin/env python3
import math
from typing import List, Dict

def delta_crux_scalar(values: List[float], crux_index: int = None) -> Dict[str, float]:
    """
    Compute the Delta Crux Math Scalar.
    
    - values: list of floats (your sequence, fold values, etc.)
    - crux_index: optional index for the 'crux' (default = midpoint).
    
    Returns a dict with:
      - crux_value: value at the pivot point
      - delta: average change around the pivot
      - scalar: normalized ratio (delta / |crux_value|)
    """
    if not values:
        raise ValueError("Values list cannot be empty.")

    n = len(values)
    if crux_index is None:
        crux_index = n // 2  # default: center pivot
    
    if not (0 <= crux_index < n):
        raise IndexError("crux_index out of range.")

    crux_value = values[crux_index]

    # compute deltas around the crux
    deltas = []
    for i, v in enumerate(values):
        if i != crux_index:
            deltas.append(v - crux_value)
    
    avg_delta = sum(deltas) / len(deltas) if deltas else 0.0
    
    # normalized scalar
    scalar = avg_delta / (abs(crux_value) if crux_value != 0 else 1.0)

    return {
        "crux_value": crux_value,
        "avg_delta": avg_delta,
        "scalar": scalar
    }


# ---------- EXAMPLE ----------
if __name__ == "__main__":
    data = [5, 7, 9, 11, 15, 20, 25]
    result = delta_crux_scalar(data, crux_index=3)
    print("Delta Crux Scalar Result:", result)