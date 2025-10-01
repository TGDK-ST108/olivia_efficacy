import math

# Fixed constant from your expression:
# 1*2*12*66440*(7/(3*2)) = 1,860,320
CONST = 1_860_320
LOG10_CONST = math.log10(CONST) + 144*math.log10(3)
LOG10_PI = math.log10(math.pi)

def leading_digits_from_log10(log10x, m=6):
    frac = log10x - math.floor(log10x)
    return int((10**frac) * 10**(m-1))

def iterate_duoquadratalize(k0=21, steps=6):
    k = k0
    out = []
    for n in range(steps):
        log10E = LOG10_CONST + k*LOG10_PI
        digits = int(math.floor(log10E)) + 1
        lead6 = leading_digits_from_log10(log10E, 6)
        out.append({
            "repeat": n,
            "k": k,
            "digits": digits,
            "leading6": lead6
        })
        # wash/repeat -> exponent doubling
        k *= 2
    return out

if __name__ == "__main__":
    rows = iterate_duoquadratalize(k0=21, steps=6)
    for r in rows:
        print(f"n={r['repeat']:>2} | k={r['k']:>4} | digits≈{r['digits']:>4} | leading6={r['leading6']:06d}")