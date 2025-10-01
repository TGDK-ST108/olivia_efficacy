def staged_rings(epoch_len=60, stages=3, base_primes=(1000,2000,3000), width=40):
    """
    Build staged prime rings around target centers.
    Each stage gets its own ascending ring.
    """
    def is_prime(n):
        if n < 2: return False
        if n % 2 == 0: return n == 2
        r = int(n**0.5)
        for i in range(3, r+1, 2):
            if n % i == 0: return False
        return True
    def nearby_primes(center, width, count=4):
        cand = []
        for x in range(center-width, center+width+1):
            if is_prime(x):
                cand.append((abs(x-center), x))
        return [x for _,x in sorted(cand)[:count]]
    rings = [nearby_primes(c, width) for c in base_primes]
    stage_len = epoch_len // stages
    return rings, stage_len

def run_staged(k_init, stages=3, epoch_len=60, base_primes=(1000,2000,3000), tau=3):
    rings, stage_len = staged_rings(epoch_len, stages, base_primes)
    k = list(k_init)
    hist = []
    stage = 0
    ES_window = []
    pll = PLLController()
    dpi = DigitPI()
    ring_shift = 0
    for t in range(epoch_len):
        m_ring = rings[stage]
        m = m_ring[(t % len(m_ring) + ring_shift) % len(m_ring)]
        phases = [phase_of_k(x) for x in k]
        digits = [digits_of_k(x) for x in k]
        ES = epoch_sympathiser(phases)
        ES_window.append(ES)
        if len(ES_window) > 5: ES_window.pop(0)
        ES_mean = sum(ES_window)/len(ES_window)
        D_t = round(mean(digits))
        # controllers
        b,q = pll.update(ES_mean)
        rshift, bbias = dpi.update(D_t, 100+((t/epoch_len)*300)) # ramp 100->400
        ring_shift = (ring_shift+rshift) % len(m_ring)
        b_eff = b+bbias
        # update ks
        kick = (t % tau == 0)
        a = pinned_root(m) if kick else None
        new_k=[]
        for x in k:
            if kick: x=(pow(a,q,m)*x)%m or 1
            else:    x=(x+b_eff)%m
            new_k.append(x)
        k=new_k
        hist.append({"t":t,"stage":stage,"m":m,"ES":ES,"D":D_t})
        # stage advancement check
        if (t+1)%stage_len==0 and stage<stages-1 and ES_mean>=0.92:
            stage+=1
    return hist