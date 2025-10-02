#!/usr/bin/env python3
import math
import hashlib
from typing import List, Dict

# ---------- CORE ----------
def delta_crux_scalar(values: List[float], crux_index: int = None) -> Dict[str, object]:
    """
    Compute the Delta Crux Math Scalar and seal it as a symbolic pact-token.
    
    - values: list of floats
    - crux_index: optional index for the 'crux' (default = midpoint)
    
    Returns:
      - crux_value: pivot value
      - avg_delta: average delta from pivot
      - scalar: normalized ratio (avg_delta / |crux_value|)
      - pact_token: sealed hex digest binding scalar to values
    """
    if not values:
        raise ValueError("Values list cannot be empty.")

    n = len(values)
    if crux_index is None:
        crux_index = n // 2  # default: midpoint

    if not (0 <= crux_index < n):
        raise IndexError("crux_index out of range.")

    crux_value = values[crux_index]

    # Deltas around pivot
    deltas = [v - crux_value for i, v in enumerate(values) if i != crux_index]
    avg_delta = sum(deltas) / len(deltas) if deltas else 0.0

    # Scalar normalization
    scalar = avg_delta / (abs(crux_value) if crux_value != 0 else 1.0)

    # Pact-token: seal the state with SHA256
    raw_string = f"{values}|crux={crux_value}|scalar={scalar:.6f}"
    pact_token = hashlib.sha256(raw_string.encode()).hexdigest()

    return {
        "crux_value": crux_value,
        "avg_delta": avg_delta,
        "scalar": scalar,
        "pact_token": pact_token
    }

# ---------- EXAMPLE ----------
if __name__ == "__main__":
    data = [5, 7, 9, 11, 15, 20, 25]
    result = delta_crux_scalar(data, crux_index=3)
    print("Delta Crux Scalar Result:")
    for k, v in result.items():
        print(f"  {k}: {v}")