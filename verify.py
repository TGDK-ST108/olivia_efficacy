import math
from statistics import mean, median

# ---- constants for your expression E = C * 3^144 * pi^k ----
C = 1_860_320
LOG10C = math.log10(C) + 144 * math.log10(3)
LOG10PI = math.log10(math.pi)

def phase_metric_from_k(k):  # PM = phi ∈ [0,1)
    lam = LOG10C + k * LOG10PI
    return lam - math.floor(lam)

def digits_from_k(k):
    lam = LOG10C + k * LOG10PI
    return int(math.floor(lam)) + 1

def epoch_sympathiser(phases):  # circular resultant length
    if not phases: return 0.0
    sx = sum(math.cos(2*math.pi*p) for p in phases)
    sy = sum(math.sin(2*math.pi*p) for p in phases)
    return math.hypot(sx, sy) / len(phases)

def normalize_series(xs):
    lo, hi = min(xs), max(xs)
    if hi == lo: return [0.0]*len(xs), lo, hi
    return [(x-lo)/(hi-lo) for x in xs], lo, hi

def tally_epoch(k_groups_per_t, weights=(0.4,0.4,0.2)):
    eff_digits, forces, ES = [], [], []
    for k_group in k_groups_per_t:
        phases = [phase_metric_from_k(k) for k in k_group]
        digits = [digits_from_k(k) for k in k_group]
        D_t = round(mean(digits))
        phi_t = mean(phases)
        eff_digits.append(D_t)
        forces.append(10_000 * D_t + int(1_000_000 * phi_t))
        ES.append(epoch_sympathiser(phases))
    D_min, D_max = min(eff_digits), max(eff_digits)
    Eff_norm = [(D - D_min)/(D_max - D_min) if D_max>D_min else 0.0 for D in eff_digits]
    Force_norm, _, _ = normalize_series(forces)
    wE, wF, wS = weights
    met_norm = wE*mean(Eff_norm) + wF*mean(Force_norm) + wS*mean(ES)
    return {
        "normalized_metScore": met_norm,
        "expanded": {
            "force_mean": mean(forces),
            "force_median": median(forces),
            "ES_mean": mean(ES),
            "ES_median": median(ES),
            "D_min": D_min,
            "D_max": D_max
        }
    }

# --- EXAMPLE: replace with your adjusted k-groups per step (each inner list = formations at that step)
epoch_k = [
    # t0..t4 toy example (phase-lock every 3rd step, additive otherwise)
    [21, 33, 55],     # t0
    [28, 40, 62],     # t1
    [35, 47, 69],     # t2  <-- multiplicative lock next step (τ=3)
    [91, 143, 221],   # t3  (synced mul kick)
    [98, 150, 228],   # t4
    [105, 157, 235],  # t5
    [277, 413, 655],  # t6  (synced mul kick)
]

if __name__ == "__main__":
    out = tally_epoch(epoch_k, weights=(0.4,0.4,0.2))
    print("normalized_metScore =", round(out["normalized_metScore"], 4))
    print("expanded:", out["expanded"])