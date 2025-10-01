import math
from statistics import mean, median

# Constants for your expression:
C = 1_860_320
LOG10C = math.log10(C) + 144 * math.log10(3)
LOG10PI = math.log10(math.pi)

def phase_metric_from_k(k):  # PM = phi in [0,1)
    lam = LOG10C + k * LOG10PI
    return lam - math.floor(lam)  # frac(lam)

def digits_from_k(k):
    lam = LOG10C + k * LOG10PI
    return int(math.floor(lam)) + 1

def epoch_sympathiser(phases):  # ES via circular resultant length
    if not phases:
        return 0.0
    sx = sum(math.cos(2*math.pi*p) for p in phases)
    sy = sum(math.sin(2*math.pi*p) for p in phases)
    R = math.hypot(sx, sy) / len(phases)
    return R  # in [0,1]

def normalize_series(xs):
    lo, hi = min(xs), max(xs)
    if hi == lo:  # avoid div-by-zero
        return [0.0 for _ in xs], lo, hi
    return [(x - lo) / (hi - lo) for x in xs], lo, hi

def tally_epoch(k_groups_per_t, weights=(0.4, 0.4, 0.2)):
    """
    k_groups_per_t: list over time t of groups at that step.
      Each entry is a list of k's (one per unit/formation) at time t.
    Returns summary dict with metScores.
    """
    eff_list, force_list, es_list = [], [], []

    # Build per-time aggregates
    for k_group in k_groups_per_t:
        # per-unit phases & digits
        phases = [phase_metric_from_k(k) for k in k_group]
        digits = [digits_from_k(k) for k in k_group]

        # pick a representative per-time D, phi (e.g., mean)
        D_t = round(mean(digits))
        phi_t = mean(phases)
        Eff_t = (D_t, phi_t)  # hold for now

        # store aggregates
        eff_list.append(D_t)
        force_list.append(10_000 * D_t + int(1_000_000 * phi_t))
        es_list.append(epoch_sympathiser(phases))

    # Normalize efficacy by digits span across epoch
    D_min, D_max = min(eff_list), max(eff_list)
    Eff_norm = [(D - D_min) / (D_max - D_min) if D_max > D_min else 0.0 for D in eff_list]

    # Normalize force to [0,1] for the normalized lens blend
    Force_norm, F_lo, F_hi = normalize_series(force_list)

    # Averages for normalized metScore
    wE, wF, wS = weights
    met_norm = wE * mean(Eff_norm) + wF * mean(Force_norm) + wS * mean(es_list)

    # Expanded lens (report raw stats)
    expanded = {
        "force_mean": mean(force_list),
        "force_median": median(force_list),
        "ES_mean": mean(es_list),
        "ES_median": median(es_list),
        "D_min": D_min,
        "D_max": D_max
    }

    return {
        "normalized_metScore": met_norm,
        "expanded": expanded,
        "per_t": {
            "Eff_norm": Eff_norm,
            "Force": force_list,
            "ES": es_list
        }
    }

# --- Example usage (3 formations across 5 steps):
if __name__ == "__main__":
    # k values per time t for three formations (toy sample)
    epoch_k = [
        [21, 33, 55],
        [63, 70, 77],
        [126, 109, 140],
        [243, 251, 260],
        [410, 397, 389],
    ]
    out = tally_epoch(epoch_k)
    print("normalized_metScore =", round(out["normalized_metScore"], 4))
    print("expanded:", out["expanded"])