import math, hashlib, json
from dataclasses import dataclass
from typing import List, Dict

# --------------------------
# Constants
# --------------------------
SQRT_RATIO = 4.39
NUM_PYRAMIDS = 4
CAP_ROTATE_DEGREES = 45.0
TICK_MULTIPLE = 0.0102

# QUMA map for non-standard hex
QUMA_MAP = {
    '0':'Q','1':'X','2':'M','3':'H','4':'A','5':'V','6':'E','7':'R','8':'S','9':'O',
    'a':'L','b':'I','c':'G','d':'T','e':'U','f':'N'
}

# --------------------------
# Utility functions
# --------------------------
def quma_seal(obj: Dict, salt: str="QUMA") -> str:
    """
    Seal an object into a QUMA non-standard digest.
    """
    j = json.dumps(obj, sort_keys=True, separators=(',',':'))
    h = hashlib.sha256((j + salt).encode()).hexdigest()
    return ''.join(QUMA_MAP[ch] for ch in h)

@dataclass
class Pyramid:
    name: str
    mass: float
    bias: float

@dataclass
class Capacitor:
    residual: float
    angle_deg: float
    tri_delta: List[float]
    seal: str  # sealed QUMA digest

class KernelAllocator:
    def __init__(self, sqrt_ratio: float = SQRT_RATIO):
        self.sqrt_ratio = sqrt_ratio
        self.angle = 0.0

    def _weights(self) -> List[float]:
        r = self.sqrt_ratio
        w = [r, 1/r, r/2.0, 1/(2.0*r)]
        s = sum(w)
        return [wi/s for wi in w]

    def allocate(self, raw_mass: float, standard_bias: List[float] = None) -> Dict[str, object]:
        w = self._weights()
        if standard_bias and len(standard_bias) == 4:
            w = [wi*bi for wi,bi in zip(w, standard_bias)]
            s = sum(w)
            w = [wi/s for wi in w]

        pyramids = []
        allocated = 0.0
        for i in range(NUM_PYRAMIDS):
            mass_i = raw_mass * w[i]
            pyramids.append(Pyramid(name=f"P{i+1}", mass=mass_i, bias=(standard_bias[i] if standard_bias else 1.0)))
            allocated += mass_i

        residual = max(0.0, raw_mass - allocated)
        tri = [residual/3.0]*3

        # create QUMA seal for capacitor
        cap_state = {"residual": round(residual,6), "angle": round(self.angle,6), "tri": [round(v,6) for v in tri]}
        cap_seal = quma_seal(cap_state, salt="POND-TILE")

        cap = Capacitor(residual=residual, angle_deg=self.angle, tri_delta=tri, seal=cap_seal)
        return {"pyramids": pyramids, "capacitor": cap, "weights": w}

    def tick_counter_rotation(self, ticks: int = 1) -> float:
        self.angle = (self.angle + CAP_ROTATE_DEGREES * (ticks * TICK_MULTIPLE)) % 360.0
        return self.angle

# --------------------------
# Demo
# --------------------------
if __name__ == "__main__":
    allocator = KernelAllocator()
    raw = 1000.0

    out = allocator.allocate(raw)
    print("== Pyramid Allocation ==")
    for p in out["pyramids"]:
        print(f"{p.name}: mass={p.mass:.4f}, bias={p.bias}")

    cap = out["capacitor"]
    print("\n== Capacitor ==")
    print(f"residual: {cap.residual:.4f}")
    print(f"tri-delta lanes: {', '.join(f'{v:.4f}' for v in cap.tri_delta)}")
    print(f"angle: {cap.angle_deg:.4f}")
    print(f"seal: {cap.seal[:48]}...")  # show prefix of seal

    allocator.tick_counter_rotation(10)
    out2 = allocator.allocate(raw)
    print(f"\nAfter 10 ticks, updated angle: {out2['capacitor'].angle_deg:.4f}")
    print(f"new seal: {out2['capacitor'].seal[:48]}...")