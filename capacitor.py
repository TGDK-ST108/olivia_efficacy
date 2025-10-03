import math, hashlib

F = 1*2*12*66440 * ((math.pi**21)*7/(4*3*13.333)) * (3**3)  # ≈ 5.189683481767861e16
log10F = math.log10(F)
L1 = 1880*log10F                         # 31424.4648376
L2 = math.log10(L1)                      # 4.4972678903
L3 = math.log10(L2)                      # 0.6529487581

mantissa = 10**(L1 - int(L1))
sci = f"{mantissa:.15f}e{int(L1)}"       # "2.916336516061447e31424"

QUMA_MAP = {'0':'Q','1':'X','2':'M','3':'H','4':'A','5':'V','6':'E','7':'R','8':'S','9':'O',
            'a':'L','b':'I','c':'G','d':'T','e':'U','f':'N'}
def quma(s, salt="TERAQIT-1880"):
    h = hashlib.sha256((s+salt).encode()).hexdigest()
    return ''.join(QUMA_MAP[ch] for ch in h)

seal = quma(sci)