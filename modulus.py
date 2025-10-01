import math

CONST = 1_860_320
LOG10_CONST = math.log10(CONST) + 144*math.log10(3)
LOG10_PI = math.log10(math.pi)

def leading_digits_from_log10(log10x, m=6):
    frac = log10x - math.floor(log10x)
    return int((10**frac) * 10**(m-1))

def next_prime(n):
    def is_prime(x):
        if x < 2: return False
        if x in (2,3): return True
        if x % 2 == 0: return False
        r = int(x**0.5)
        for i in range(3, r+1, 2):
            if x % i == 0: return False
        return True
    p = n+1
    while not is_prime(p):
        p += 1
    return p

def evolve_dynamic(k0=21, steps=20):
    k = k0
    rows = []
    for t in range(steps):
        log10E = LOG10_CONST + k * LOG10_PI
        digits = int(math.floor(log10E)) + 1
        lead6 = leading_digits_from_log10(log10E, 6)

        rows.append({"t": t, "k": k, "digits": digits, "leading6": lead6})

        # ----- Dynamic allocation rules -----
        m = next_prime(k + t)   # modulus depends on time & state
        if t % 2 == 0:          # even steps: additive
            k = (k + 7) % m
        else:                   # odd steps: multiplicative
            k = (3 * k) % m
    return rows

if __name__ == "__main__":
    out = evolve_dynamic()
    for r in out:
        print(f"t={r['t']:>2} | k={r['k']:>5} | digits≈{r['digits']:>4} | leading6={r['leading6']:06d}")