import math

# ---------- constants ----------
CONST = 1_860_320
LOG10_CONST = math.log10(CONST) + 144 * math.log10(3)
LOG10_PI = math.log10(math.pi)

# ---------- helpers ----------
def leading_digits_from_log10(log10x, m=6):
    frac = log10x - math.floor(log10x)
    return int((10**frac) * 10**(m-1)), frac  # returns (leading_m_digits, mantissa)

def is_prime(n: int) -> bool:
    if n < 2: return False
    if n in (2,3): return True
    if n % 2 == 0: return False
    r = int(n**0.5)
    for i in range(3, r+1, 2):
        if n % i == 0: return False
    return True

def next_prime(n: int) -> int:
    p = max(2, n+1)
    if p % 2 == 0 and p != 2: p += 1
    while not is_prime(p):
        p += 2 if p > 2 else 1
    return p

def prime_factors(n: int):
    f, x = set(), n
    d = 2
    while d * d <= x:
        while x % d == 0:
            f.add(d); x //= d
        d = 3 if d == 2 else d + 2
    if x > 1: f.add(x)
    return f

def is_primitive_root(a: int, p: int) -> bool:
    if not is_prime(p): return False
    phi = p - 1
    for q in prime_factors(phi):
        if pow(a, phi // q, p) == 1:
            return False
    return True

def find_primitive_root(p: int) -> int:
    for a in range(2, p):
        if is_primitive_root(a, p):
            return a
    raise RuntimeError("No primitive root found (should not happen for prime p).")

# ---------- DAC engine ----------
class DAC:
    def __init__(self,
                 k0=21,
                 steps=32,
                 modulus_mode="prime_follow",  # 'prime_follow' | 'prime_ring' | 'epoch_fixed'
                 prime_ring=(997, 1009, 1013),
                 epochs=((0, 999999),),        # (start,end) with a single fixed prime via epoch_param
                 epoch_param=1009,
                 mu=0, rho=0,
                 update_policy="parity_switch",  # 'parity_switch' | 'time_switch' | 'phase_gated'
                 tau=4, phase_interval=(0.0, 0.5),
                 add_b=7, mul_a=None
                 ):
        self.k = k0
        self.steps = steps
        self.modulus_mode = modulus_mode
        self.prime_ring = tuple(prime_ring)
        self.epochs = tuple(epochs)
        self.epoch_param = epoch_param
        self.mu = mu
        self.rho = rho
        self.update_policy = update_policy
        self.tau = tau
        self.phase_interval = phase_interval
        self.add_b = add_b
        self.mul_a = mul_a  # if None, we pick primitive root per step

        # validate prime sources
        if self.modulus_mode == "prime_ring":
            for p in self.prime_ring:
                if not is_prime(p):
                    raise ValueError("All primes in prime_ring must be prime.")
        if self.modulus_mode == "epoch_fixed":
            if not is_prime(self.epoch_param):
                raise ValueError("epoch_param must be prime for epoch_fixed.")

    def choose_modulus(self, t):
        if self.modulus_mode == "prime_follow":
            return next_prime(self.k + t + self.mu)
        elif self.modulus_mode == "prime_ring":
            idx = (t + self.rho) % len(self.prime_ring)
            return self.prime_ring[idx]
        elif self.modulus_mode == "epoch_fixed":
            # single-epoch example; extend if you maintain multiple primes by epoch range
            return self.epoch_param
        else:
            raise ValueError("Unknown modulus_mode")

    def choose_update_operator(self, t, phi, m):
        # returns ("add", b) or ("mul", a)
        if self.update_policy == "parity_switch":
            if self.k % 2 == 0:
                return ("add", self.add_b)
            else:
                a = self.mul_a or find_primitive_root(m)
                return ("mul", a)
        elif self.update_policy == "time_switch":
            if t % self.tau == 0:
                a = self.mul_a or find_primitive_root(m)
                return ("mul", a)
            else:
                return ("add", self.add_b)
        elif self.update_policy == "phase_gated":
            lo, hi = self.phase_interval
            if lo <= phi < hi:
                a = self.mul_a or find_primitive_root(m)
                return ("mul", a)
            else:
                return ("add", self.add_b)
        else:
            raise ValueError("Unknown update_policy")

    def step(self, t):
        # Observables before update
        log10E = LOG10_CONST + self.k * LOG10_PI
        digits = int(math.floor(log10E)) + 1
        lead6, phi = leading_digits_from_log10(log10E, m=6)
        m = self.choose_modulus(t)
        op, param = self.choose_update_operator(t, phi, m)

        # Apply update
        if op == "add":
            if math.gcd(param, m) != 1:
                raise ValueError(f"add_b={param} not coprime with m={m}")
            k_next = (self.k + param) % m
        else:
            # multiplicative
            if not is_prime(m):
                raise ValueError("Multiplicative mode expects prime modulus.")
            a = param
            if not is_primitive_root(a, m):
                # Not strictly required, but informs about period potential
                pass
            if self.k % m == 0:
                # keep k in 1..m-1 for nice multiplicative cycles
                self.k = 1
            k_next = (a * self.k) % m
            if k_next == 0:
                k_next = 1  # avoid collapsing to 0

        row = {
            "t": t, "k": self.k, "m": m, "op": op, "param": param,
            "digits": digits, "leading6": lead6, "phi": phi
        }
        self.k = k_next
        return row

    def run(self):
        trace = []
        for t in range(self.steps):
            trace.append(self.step(t))
        return trace

if __name__ == "__main__":
    # Example configuration:
    # - Dynamic prime-follow modulus
    # - Parity-based mode switch (even k -> add, odd k -> mul)
    # - Add step b=7, multiplicative uses per-step primitive root
    dac = DAC(
        k0=21,
        steps=24,
        modulus_mode="prime_follow",
        mu=0,
        update_policy="parity_switch",
        add_b=7,
        mul_a=None  # auto-pick primitive root each multiplicative step
    )
    out = dac.run()
    print("t |    k |    m |  op  | param | digits | leading6 |   phi")
    print("--+------+------+------+-------+--------+----------+--------")
    for r in out:
        print(f"{r['t']:2d}|{r['k']:6d}|{r['m']:6d}|{r['op']:^6}|{r['param']:6d}|"
              f"{r['digits']:8d}|{r['leading6']:10d}| {r['phi']:.6f}")