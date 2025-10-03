import math
from dataclasses import dataclass
from typing import List, Dict

# --- constants ---
SQRT_RATIO = 4.39                    # your asserted square-root ratio (scaling basis)
NUM_PYRAMIDS = 4
CAP_ROTATE_DEGREES = 45.0            # counter-rotation per engage
TICK_MULTIPLE = 0.0102               # frequency multiple against kernel driver

@dataclass
class Pyramid:
    name: str
    mass: float          # allocated raw mass
    bias: float          # pyramid-specific bias factor for shaping

@dataclass
class Capacitor:
    residual: float      # leftover mass
    angle_deg: float     # current counter-rotation angle
    tri_delta: List[float]  # 3-lane tri-deltalineated splits

class KernelAllocator:
    def __init__(self, sqrt_ratio: float = SQRT_RATIO):
        self.sqrt_ratio = sqrt_ratio
        self.angle = 0.0  # capacitor counter-rotation state

    def _weights(self) -> List[float]:
        """
        4 pyramids get weights derived from the sqrt-ratio family.
        We use a simple normalized set around r and 1/r to keep symmetry.
        """
        r = self.sqrt_ratio
        w = [r, 1/r, r/2.0, 1/(2.0*r)]
        s = sum(w)
        return [wi/s for wi in w]

    def allocate(self, raw_mass: float, standard_bias: List[float] = None) -> Dict[str, object]:
        """
        Split 'raw_mass' into 4 pyramids (weighted), then send the residual to the
        tri-deltalineated kernel capacitor (3 equal lanes by default).
        """
        w = self._weights()
        if standard_bias and len(standard_bias) == 4:
            # apply optional pyramid biases then renormalize
            w = [wi*bi for wi,bi in zip(w, standard_bias)]
            s = sum(w)
            w = [wi/s for wi in w]

        # allocate to pyramids
        pyramids = []
        allocated = 0.0
        for i in range(NUM_PYRAMIDS):
            mass_i = raw_mass * w[i]
            pyramids.append(Pyramid(name=f"P{i+1}", mass=mass_i, bias=(standard_bias[i] if standard_bias else 1.0)))
            allocated += mass_i

        residual = max(0.0, raw_mass - allocated)

        # tri-deltalineate residual into 3 equal lanes (you can bias later)
        tri = [residual/3.0]*3
        cap = Capacitor(residual=residual, angle_deg=self.angle, tri_delta=tri)
        return {"pyramids": pyramids, "capacitor": cap, "weights": w}

    def tick_counter_rotation(self, ticks: int = 1) -> float:
        """
        Advance the capacitor by CAP_ROTATE_DEGREES counter to the kernel driver
        every 'engage' where the driver tick matches the 0.0102 multiple.
        Here we model: angle += 45° * ticks * 0.0102 (mod 360)
        """
        self.angle = (self.angle + CAP_ROTATE_DEGREES * (ticks * TICK_MULTIPLE)) % 360.0
        return self.angle

# --- demo ---
if __name__ == "__main__":
    raw = 1000.0  # example raw data mass
    allocator = KernelAllocator()

    # initial allocation
    out = allocator.allocate(raw)
    print("== Allocation with √ ratio 4.39 ==")
    for p in out["pyramids"]:
        print(f" {p.name}: mass={p.mass:.4f}, bias={p.bias}")
    cap = out["capacitor"]
    print(f" residual -> capacitor: {cap.residual:.4f}")
    print(f" capacitor tri-delta lanes: {', '.join(f'{v:.4f}' for v in cap.tri_delta)}")
    print(f" capacitor angle (deg): {cap.angle_deg:.4f}")

    # advance kernel driver by 10 ticks; capacitor counter-rotates
    angle = allocator.tick_counter_rotation(ticks=10)
    print(f"\nAfter 10 ticks (counter-rotation @ 45° * 0.0102 per tick): angle={angle:.4f}°")

    # re-check allocation after rotation (mass allocation unaffected; angle updated)
    out2 = allocator.allocate(raw)
    print(f" updated capacitor angle carried: {out2['capacitor'].angle_deg:.4f}°")