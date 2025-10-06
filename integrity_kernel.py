import math
from typing import Dict

# ---------- Integrity Kernel (xyjr · K) ----------
# K = (pi^21) * (7/12) * (3^3)
_K = (math.pi ** 21) * (7.0 / 12.0) * (3 ** 3)

def integrity_kernel(x: float, y: float, j: float, r: float,
                     mu_log10: float = 9.0,
                     sigma_log10: float = 2.0) -> Dict[str, float]:
    """
    Compute Integrity using the TGDK 'xyjr(pi^21×7/4/3/1)3^3' form.

    Parameters
    ----------
    x, y, j, r : float
        Component vectors feeding the integrity axis.
    mu_log10 : float
        Center for the log-scale sigmoid (in base-10); shifts the midpoint.
    sigma_log10 : float
        Spread for the log-scale sigmoid; larger -> softer slope.

    Returns
    -------
    dict
        {
          "integrity_raw": float,         # xyjr * K (may be huge)
          "integrity_norm": float,        # [0,1] logistic on log10 scale
          "integrity_force": int          # >= 10_000, expanded-force lens
        }

    Notes
    -----
    - integrity_raw = (x*y*j*r) * K
    - integrity_norm = sigmoid( (log10(integrity_raw) - mu)/sigma )
        where sigmoid(z) = 1 / (1 + e^-z)
    - integrity_force = 10_000 + floor(90_000 * integrity_norm)
      (maps 0..1 -> 10k..100k)
    """
    # Guard: nonpositive base collapses integrity to 0 safely.
    base = x * y * j * r
    if base <= 0:
        return {"integrity_raw": 0.0, "integrity_norm": 0.0, "integrity_force": 10_000}

    integrity_raw = base * _K

    # Log-sigmoid normalization on base-10 scale for stability
    log10_val = math.log10(integrity_raw)
    z = (log10_val - mu_log10) / sigma_log10
    integrity_norm = 1.0 / (1.0 + math.exp(-z))

    # Expanded-force lens (always >= 10k)
    integrity_force = 10_000 + int(math.floor(90_000 * integrity_norm + 1e-9))

    return {
        "integrity_raw": integrity_raw,
        "integrity_norm": integrity_norm,
        "integrity_force": integrity_force,
    }

# ---------- Example ----------
# Tune mu/sigma if your typical xyjr scale is different.
# result = integrity_kernel(1.0, 1.0, 1.0, 1.0)
# print(result)