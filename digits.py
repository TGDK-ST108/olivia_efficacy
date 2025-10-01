import math
from statistics import mean

# --- constants ---
C = 1_860_320
LOG10C = math.log10(C) + 144 * math.log10(3)
LOG10PI = math.log10(math.pi)

def phase_metric_from_k(k):
    lam = LOG10C + k * LOG10PI
    return lam - math.floor(lam)

def digits_from_k(k):
    lam = LOG10C + k * LOG10PI
    return int(math.floor(lam)) + 1

def epoch_sympathiser(phases):
    if not phases: return 0.0
    sx = sum(math.cos(2*math.pi*p) for p in phases)
    sy = sum(math.sin(2*math.pi*p) for p in phases)
    return math.hypot(sx, sy) / len(phases)

# --- primitive root (simple) ---
def factors(n):
    f, d = set(), 2
    while d * d <= n:
        while n % d == 0: f.add(d); n//=d
        d = 3 if d==2 else d+2
    if n>1: f.add(n)
    return f

def is_primitive_root(a, p):
    phi = p-1
    return all(pow(a, phi//q, p) != 1 for q in factors(phi))

def find_primitive_root(p):
    for g in range(2, p):
        if is_primitive_root(g, p): return g
    raise RuntimeError("no primitive root found")

# --- Lever 1 cache ---
PINNED_ROOTS = {}
def pinned_root(p):
    if p not in PINNED_ROOTS:
        PINNED_ROOTS[p] = find_primitive_root(p)
    return PINNED_ROOTS[p]

# --- Lever 3 controller ---
ES_TARGET = 0.90
def nudge_b(es_mean, b, base=7, lo=-1, hi=+1):
    if es_mean < ES_TARGET - 0.02 and b < base + hi:  return b + 1
    if es_mean > ES_TARGET + 0.02 and b > base + lo:  return b - 1
    return b

def step_formations(k_list, m, t, tau, add_b):
    """
    One time step for all formations sharing the same modulus m at t.
    τ = cadence; every τ-th step do multiplicative (phase-lock), else additive.
    """
    next_k, phases, digits = [], [], []
    mul_kick = (t % tau == 0)
    a = pinned_root(m) if mul_kick else None
    for k in k_list:
        if mul_kick:
            k = (a * k) % m or 1
        else:
            k = (k + add_b) % m
        next_k.append(k)
        p = phase_metric_from_k(k)
        d = digits_from_k(k)
        phases.append(p); digits.append(d)
    ES_t = epoch_sympathiser(phases)
    D_t  = round(mean(digits))
    return next_k, ES_t, D_t

# --- example drive (plug in your ring & epochs) ---
def run_campaign(k_init, ring, steps=30, tau=3, add_b=7):
    k = list(k_init)
    ES_hist, D_hist = [], []
    for t in range(steps):
        m = ring[t % len(ring)]       # Lever 2: ascending ring recommended
        k, ES_t, D_t = step_formations(k, m, t, tau, add_b)
        ES_hist.append(ES_t); D_hist.append(D_t)
        # Lever 3: adapt add_b slightly based on ES
        add_b = nudge_b(ES_t, add_b)
    return {"ES_mean": mean(ES_hist), "D_min": min(D_hist), "D_max": max(D_hist)}

# --------- USAGE ---------
if __name__ == "__main__":
    ring = [983, 997, 1009, 1013]   # ascending ring (Lever 2)
    k0   = [21, 33, 55]             # three formations
    out  = run_campaign(k0, ring, steps=60, tau=3, add_b=7)
    print(out)