"""
Octup-Quadrolineated Throughput Engine
- 4 quadrants: Cost, Revenue, Overhead, Growth  (the pyramids)
- 8 lanes per quadrant  => 32 concurrent lanes
- Lane capacity modulated by:
    * pyramid mass share (from √ ratio 4.39 allocation)
    * capacitor counter-rotation (45° * 0.0102 * ticks) => sinusoidal gating
    * per-quadrant weights (priority / throttling)
- Backpressure + fairness (round-robin within quadrant)
- Returns a tick schedule (who moves now) + updated state
"""

from dataclasses import dataclass, field
from typing import Dict, List, Deque, Tuple
from collections import deque
import math, time

# ---- import allocator from previous step (paste its class here if running standalone) ----
# from kernel_allocator import KernelAllocator, SQRT_RATIO

SQRT_RATIO = 4.39
CAP_ROTATE_DEGREES = 45.0
TICK_MULTIPLE = 0.0102

QUADRANTS = ["Cost", "Revenue", "Overhead", "Growth"]
LANES_PER_QUAD = 8

@dataclass
class Lane:
    id: str
    queue: Deque[dict] = field(default_factory=deque)  # items: {"id":..., "weight":...}
    active: bool = True

@dataclass
class Quadrant:
    name: str
    lanes: List[Lane]
    priority: float = 1.0   # external bias knob (e.g., prioritize Revenue > Cost)
    mass_share: float = 0.25  # filled by allocator
    rr_idx: int = 0

class OctupQuadEngine:
    def __init__(self, allocator):
        self.alloc = allocator
        self.tick = 0
        # build 4x8 lanes
        self.quads: Dict[str, Quadrant] = {}
        for q in QUADRANTS:
            lanes = [Lane(id=f"{q[:1]}{i}") for i in range(LANES_PER_QUAD)]
            self.quads[q] = Quadrant(name=q, lanes=lanes)

        # default priorities (tune as needed)
        self.quads["Revenue"].priority = 1.25
        self.quads["Growth"].priority  = 1.10
        self.quads["Cost"].priority    = 0.95
        self.quads["Overhead"].priority= 0.80

    # --- public API ---
    def enqueue(self, quadrant: str, item: dict, lane_hint: int | None = None):
        """Add an item into a quadrant. If lane_hint is None, use shortest queue."""
        q = self.quads[quadrant]
        if lane_hint is None:
            tgt = min(q.lanes, key=lambda L: len(L.queue))
        else:
            tgt = q.lanes[lane_hint % LANES_PER_QUAD]
        tgt.queue.append(item)

    def snapshot_load(self) -> Dict[str, int]:
        return {q: sum(len(L.queue) for L in self.quads[q].lanes) for q in QUADRANTS}

    def step(self, raw_mass: float) -> Dict:
        """
        One scheduler tick:
         - refresh pyramid mass shares from allocator
         - compute lane capacities via rotation modulation
         - select items per lane using RR within each quadrant
        """
        self.tick += 1

        # 1) refresh mass shares from allocator (keeps finance binding live)
        out = self.alloc.allocate(raw_mass)
        weights = out["weights"]         # order: P1..P4 (map to Cost, Revenue, Overhead, Growth)
        map_order = ["Cost","Revenue","Overhead","Growth"]
        for name, w in zip(map_order, weights):
            self.quads[name].mass_share = w

        # 2) rotation modulation factor from capacitor angle
        angle = self.alloc.tick_counter_rotation(1)  # updates internal angle
        # normalized gating 0..1 (use raised cosine for smoothness), counter to driver
        gate = 0.5 * (1 + math.cos(math.radians(angle)))  # 1 at 0°, 0 at 180°
        # emphasize 0.0102 multiple as micro-throttle
        micro = 1.0 - (TICK_MULTIPLE * 0.5)
        rot_mod = max(0.05, gate * micro)  # never fully 0

        # 3) per-quadrant capacity this tick
        # base capacity = 8 lanes * mass_share * priority * rot_mod
        quad_caps: Dict[str, float] = {}
        for q in QUADRANTS:
            base = LANES_PER_QUAD * self.quads[q].mass_share * self.quads[q].priority * rot_mod
            quad_caps[q] = max(0.5, base)  # minimum pulse capacity

        # 4) schedule: pull up to capacity items (weights act as unit costs here)
        schedule: List[Tuple[str,str,dict]] = []  # (quadrant, lane_id, item)
        for q in QUADRANTS:
            cap = quad_caps[q]
            qd = self.quads[q]
            pulled = 0.0
            # round-robin across lanes
            lane_indices = list(range(LANES_PER_QUAD))
            start = qd.rr_idx % LANES_PER_QUAD
            lane_indices = lane_indices[start:] + lane_indices[:start]

            for idx in lane_indices:
                if pulled >= cap:
                    break
                L = qd.lanes[idx]
                if not L.active or not L.queue:
                    continue
                item = L.queue[0]
                w = float(item.get("weight", 1.0))
                if pulled + w <= cap:
                    schedule.append((q, L.id, L.queue.popleft()))
                    pulled += w

            qd.rr_idx = (start + 1) % LANES_PER_QUAD  # advance RR head

        return {
            "tick": self.tick,
            "angle_deg": round(angle, 4),
            "rot_mod": round(rot_mod, 6),
            "quad_caps": {k: round(v, 3) for k,v in quad_caps.items()},
            "scheduled": schedule,
            "backlog": self.snapshot_load(),
        }

# ------------------ demo ------------------
if __name__ == "__main__":
    from math import ceil

    # minimal allocator stub (paste in the full allocator for real runs)
    class _AllocStub:
        def __init__(self): self.angle = 0.0
        def _weights(self):
            r = SQRT_RATIO; w=[r,1/r,r/2,1/(2*r)]; s=sum(w); return [wi/s for wi in w]
        def allocate(self, raw_mass): return {"weights": self._weights()}
        def tick_counter_rotation(self, ticks=1):
            self.angle = (self.angle + CAP_ROTATE_DEGREES * (ticks * TICK_MULTIPLE)) % 360.0
            return self.angle

    eng = OctupQuadEngine(_AllocStub())

    # enqueue some items
    for i in range(40):  # cost-heavy
        eng.enqueue("Cost", {"id": f"c{i}", "weight": 1})
    for i in range(30):
        eng.enqueue("Revenue", {"id": f"r{i}", "weight": 1})
    for i in range(18):
        eng.enqueue("Overhead", {"id": f"o{i}", "weight": 1})
    for i in range(26):
        eng.enqueue("Growth", {"id": f"g{i}", "weight": 1})

    # run a few ticks
    for _ in range(5):
        res = eng.step(raw_mass=1000.0)
        print(f"\nT{res['tick']:02d} angle={res['angle_deg']} rot_mod={res['rot_mod']}")
        print(" caps:", res["quad_caps"])
        print(" scheduled:", [f"{q}:{lid}:{it['id']}" for (q,lid,it) in res["scheduled"]][:10], "...")
        print(" backlog:", res["backlog"])