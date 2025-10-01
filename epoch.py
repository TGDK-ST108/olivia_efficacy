import math

# constants
CONST = 1_860_320
LOG10_CONST = math.log10(CONST) + 144 * math.log10(3)
LOG10_PI = math.log10(math.pi)

def leading_digits_from_log10(log10x, m=6):
    frac = log10x - math.floor(log10x)
    return int((10**frac) * 10**(m-1)), frac

def is_prime(n):
    if n < 2: return False
    if n in (2,3): return True
    if n % 2 == 0: return False
    r = int(n**0.5)
    for i in range(3, r+1, 2):
        if n % i == 0: return False
    return True

def find_primitive_root(p):
    def factors(n):
        f, d = set(), 2
        while d*d <= n:
            while n % d == 0: f.add(d); n//=d
            d+=1
        if n>1: f.add(n)
        return f
    phi = p-1
    for g in range(2,p):
        if all(pow(g, phi//q, p)!=1 for q in factors(phi)):
            return g
    return None

class RingEpochDAC:
    def __init__(self, k0=21, steps=30,
                 epochs=[(0,50,[997,1009,1013]), (50,100,[2003,2011,2017,2027])],
                 update_policy="parity_switch", add_b=7):
        self.k = k0
        self.steps = steps
        self.epochs = epochs
        self.update_policy = update_policy
        self.add_b = add_b

    def modulus_for_t(self,t):
        for (start,end,ring) in self.epochs:
            if start <= t < end:
                idx=(t-start)%len(ring)
                return ring[idx]
        return self.epochs[-1][2][0]

    def evolve(self):
        rows=[]
        for t in range(self.steps):
            log10E=LOG10_CONST+self.k*LOG10_PI
            digits=int(math.floor(log10E))+1
            lead6,phi=leading_digits_from_log10(log10E,6)
            m=self.modulus_for_t(t)
            # decide update
            if self.update_policy=="parity_switch":
                if self.k%2==0: # additive
                    self.k=(self.k+self.add_b)%m
                    op=("add",self.add_b)
                else: # multiplicative
                    a=find_primitive_root(m)
                    self.k=(a*self.k)%m or 1
                    op=("mul",a)
            rows.append({"t":t,"k":self.k,"m":m,"digits":digits,"leading6":lead6,"phi":phi,"op":op})
        return rows

if __name__=="__main__":
    dac=RingEpochDAC(k0=21,steps=60)
    trace=dac.evolve()
    for r in trace:
        print(f"t={r['t']:2} | m={r['m']:4} | op={r['op'][0]:>3}({r['op'][1]}) | k={r['k']:5} | "
              f"digits≈{r['digits']:4} | leading6={r['leading6']:06d}")