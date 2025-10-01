import math

# ----- Fixed numeric pieces from your expression -----
CONST = 1_860_320  # 1*2*12*66440*(7/(3*2))
LOG10_CONST = math.log10(CONST) + 144*math.log10(3)
LOG10_PI = math.log10(math.pi)

def leading_digits_from_log10(log10x, m=6):
    frac = log10x - math.floor(log10x)
    return int((10**frac) * 10**(m-1))

# ---------- Utilities for multiplicative cycles ----------
def prime_factors(n):
    """Trial division factorization of n (smallish n is fine)."""
    f, i = set(), 2
    while i * i <= n:
        while n % i == 0:
            f.add(i)
            n //= i
        i += 1 if i == 2 else 2
    if n > 1:
        f.add(n)
    return f

def is_primitive_root(a, p):
    """Check if 'a' is a primitive root modulo prime p."""
    assert p > 2 and is_prime(p)
    phi = p - 1
    factors = prime_factors(phi)
    for q in factors:
        if pow(a, phi // q, p) == 1:
            return False
    return True

def is_prime(n):
    if n < 2:
        return False
    if n in (2,3):
        return True
    if n % 2 == 0:
        return False
    r = int(n**0.5)
    for i in range(3, r+1, 2):
        if n % i == 0:
            return False
    return True

def find_primitive_root(p):
    """Find a primitive root modulo prime p (simple search)."""
    assert is_prime(p)
    for a in range(2, p):
        if is_primitive_root(a, p):
            return a
    raise ValueError("No primitive root found (should not happen for prime p).")

# ---------- Core engine ----------
def evolve_k(
    k0=21,
    steps=32,
    mode="multiplicative",  # "multiplicative" or "additive"
    m=997,                  # modulus (prime recommended)
    a=None,                 # multiplier (if multiplicative). If None, find primitive root.
    b=1                     # increment (if additive), must be coprime with m
):
    if not is_prime(m):
        raise ValueError("Pick a prime modulus m for best behavior.")
    if mode == "multiplicative":
        if a is None:
            a = find_primitive_root(m)  # guarantees period m-1 as long as k0 != 0
        if k0 % m == 0:
            raise ValueError("k0 must be in 1..m-1 for multiplicative mode.")
        update = lambda k: (a * k) % m
        theoretical_period = m - 1 if is_primitive_root(a, m) else None
    elif mode == "additive":
        if math.gcd(b, m) != 1:
            raise ValueError("For additive mode, pick b coprime with m for full period m.")
        update = lambda k: (k + b) % m
        theoretical_period = m
    else:
        raise ValueError("mode must be 'multiplicative' or 'additive'.")

    # Run and detect first repeat
    seen = {}
    k = k0 % m
    rows = []
    t = 0
    while t < steps:
        log10E = LOG10_CONST + k * LOG10_PI
        digits = int(math.floor(log10E)) + 1
        lead6 = leading_digits_from_log10(log10E, 6)
        rows.append({
            "t": t, "k": k, "digits": digits, "leading6": lead6
        })

        if k in seen:
            first = seen[k]
            detected_period = t - first
            break
        seen[k] = t
        k = update(k)
        t += 1
    else:
        detected_period = None

    return {
        "mode": mode,
        "m": m,
        "a": a if mode == "multiplicative" else None,
        "b": b if mode == "additive" else None,
        "theoretical_period": theoretical_period,
        "detected_period": detected_period,
        "trace": rows
    }

if __name__ == "__main__":
    # Example 1: multiplicative cycle with a primitive root (period = m-1)
    out1 = evolve_k(k0=21, steps=40, mode="multiplicative", m=997, a=None)  # find primitive root
    print("== Multiplicative mode ==")
    print(f"m={out1['m']}, a={out1['a']}, theoretical_period={out1['theoretical_period']}, detected_period={out1['detected_period']}")
    for r in out1["trace"]:
        print(f"t={r['t']:>2} | k={r['k']:>4} | digits≈{r['digits']:>4} | leading6={r['leading6']:06d}")

    print("\n== Additive mode ==")
    # Example 2: additive cycle (period = m) with step b=7
    out2 = evolve_k(k0=21, steps=20, mode="additive", m=997, b=7)
    print(f"m={out2['m']}, b={out2['b']}, theoretical_period={out2['theoretical_period']}, detected_period={out2['detected_period']}")
    for r in out2["trace"]:
        print(f"t={r['t']:>2} | k={r['k']:>4} | digits≈{r['digits']:>4} | leading6={r['leading6']:06d}")