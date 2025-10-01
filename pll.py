import math
from statistics import mean

# --- constants for E = C * 3^144 * pi^k ---
C = 1_860_320
LOG10C = math.log10(C) + 144 * math.log10(3)
LOG10PI = math.log10(math.pi)

def phase_of_k(k):
    lam = LOG10C + k * LOG10PI
    return lam - math.floor(lam)  # in [0,1)

def digits_of_k(k):
    lam = LOG10C + k * LOG10PI
    return int(math.floor(lam)) + 1

def epoch_sympathiser(phases):
    if not phases: return 0.0
    sx = sum(math.cos(2*math.pi*p) for p in phases)
    sy = sum(math.sin(2*math.pi*p) for p in phases)
    return math.hypot(sx, sy) / len(phases)  # R in [0,1]

# --- primitive roots ---
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

# cache pinned primitive roots (Lever 1)
PINNED_ROOTS = {}
def pinned_root(p):
    if p not in PINNED_ROOTS:
        PINNED_ROOTS[p] = find_primitive_root(p)
    return PINNED_ROOTS[p]

# --- Lever 5 controllers ---

class PLLController:
    """
    Discrete PLL: raises ES by nudging additive step b and
    multiplicative kick power q (i.e., use a^q mod m on kick steps).
    """
    def __init__(self, ES_target=0.95, k_b=1, k_q=1, b_base=7, b_bounds=(-1, +3), q_bounds=(1, 4)):
        self.ES_target = ES_target
        self.k_b = k_b  # integer gain for b nudges
        self.k_q = k_q  # integer gain for q nudges
        self.b_base = b_base
        self.b_bounds = b_bounds
        self.q_bounds = q_bounds
        self.b = b_base
        self.q = 1  # multiplicative kick power

    def update(self, ES_current):
        err = self.ES_target - ES_current  # positive if we need more lock
        # Nudge b (small, bounded)
        if err > 0.02 and self.b < self.b_base + self.b_bounds[1]:
            self.b += self.k_b
        elif err < -0.02 and self.b > self.b_base + self.b_bounds[0]:
            self.b -= self.k_b
        # Nudge q (power of primitive root on kick)
        if err > 0.05 and self.q < self.q_bounds[1]:
            self.q += self.k_q
        elif err < -0.05 and self.q > self.q_bounds[0]:
            self.q -= self.k_q
        return self.b, self.q

class DigitPI:
    """
    Tiny PI controller to track digits to a time-varying setpoint D_star[t].
    Adjusts 'ring index offset' (which prime is chosen) and can also bias b.
    """
    def __init__(self, kp=0.1, ki=0.02, bias_b_limit=1):
        self.kp = kp
        self.ki = ki
        self.acc = 0.0
        self.bias_b_limit = bias_b_limit
        self.bias_b = 0  # small integer bias added to b

    def update(self, D_current, D_star):
        e = D_star - D_current
        self.acc += e
        u = self.kp * e + self.ki * self.acc
        # Convert small control effort to integer ring offset and b bias:
        ring_shift = 0 if abs(u) < 0.5 else (1 if u > 0 else -1)
        # gentle bias on b to help track D*
        if u > 1 and self.bias_b < +self.bias_b_limit:
            self.bias_b += 1
        elif u < -1 and self.bias_b > -self.bias_b_limit:
            self.bias_b -= 1
        return ring_shift, self.bias_b

# --- engine with PLL + Digit PI ---
def run_with_pll(
    k_init,            # list of k for each formation
    ring,              # list of primes (ascending recommended)
    steps=60,
    tau=3,             # kick cadence
    D_star_start=100,  # digit setpoint ramp start
    D_star_end=430     # digit setpoint ramp end
):
    k = list(k_init)
    pll = PLLController(ES_target=0.95, k_b=1, k_q=1, b_base=7, b_bounds=(-1, +3), q_bounds=(1, 4))
    dpi = DigitPI(kp=0.12, ki=0.03, bias_b_limit=1)

    ring_idx_offset = 0
    hist = []

    for t in range(steps):
        # choose modulus with (optional) ring index shift from PI:
        base_idx = (t % len(ring))
        m = ring[(base_idx + ring_idx_offset) % len(ring)]

        # compute current phases/digits BEFORE update for control signals:
        phases = [phase_of_k(x) for x in k]
        digits = [digits_of_k(x) for x in k]
        ES = epoch_sympathiser(phases)
        D_t = round(mean(digits))

        # targets
        D_star = round(D_star_start + (D_star_end - D_star_start) * (t / max(1, steps - 1)))

        # controllers:
        b, q = pll.update(ES)  # epoch sympathiser loop
        ring_shift, b_bias = dpi.update(D_t, D_star)  # digit tracking loop
        ring_idx_offset = (ring_idx_offset + ring_shift) % len(ring)
        b_eff = b + b_bias  # effective additive step (bounded small nudge)

        # update ks:
        kick = (t % tau == 0)
        a = pinned_root(m) if kick else None
        new_k = []
        for x in k:
            if kick:
                # power kick: a^q * x (mod m), avoid 0
                x = (pow(a, q, m) * x) % m or 1
            else:
                x = (x + b_eff) % m
            new_k.append(x)
        k = new_k

        # record
        hist.append({
            "t": t, "m": m, "ES": ES, "D": D_t, "D_star": D_star,
            "b": b, "b_bias": b_bias, "q": q, "ring_shift": ring_shift
        })
    return hist

# --- example drive ---
if __name__ == "__main__":
    ring = [983, 997, 1009, 1013]    # ascending (Lever 2)
    k0   = [21, 33, 55]              # three formations
    hist = run_with_pll(k0, ring, steps=60, tau=3, D_star_start=102, D_star_end=428)
    # print a compact summary
    ES_mean = sum(h["ES"] for h in hist)/len(hist)
    D_min   = min(h["D"] for h in hist)
    D_max   = max(h["D"] for h in hist)
    print({"ES_mean": round(ES_mean,3), "D_min": D_min, "D_max": D_max})