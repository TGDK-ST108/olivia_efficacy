import math, hashlib, json
from dataclasses import dataclass, field
from typing import Dict, List, Deque, Tuple
from collections import deque

# --- QUMA map for non-standard hex ---
QUMA_MAP = {
    '0':'Q','1':'X','2':'M','3':'H','4':'A','5':'V','6':'E','7':'R','8':'S','9':'O',
    'a':'L','b':'I','c':'G','d':'T','e':'U','f':'N'
}
def quma_seal(obj: Dict, salt: str="OCTUPQ") -> str:
    j = json.dumps(obj, sort_keys=True, separators=(',',':'))
    h = hashlib.sha256((j + salt).encode()).hexdigest()
    return ''.join(QUMA_MAP[ch] for ch in h)

# --- Constants ---
SQRT_RATIO = 4.39
CAP_ROTATE_DEGREES = 45.0
TICK_MULTIPLE = 0.0102
QUADRANTS = ["Cost", "Revenue", "Overhead", "Growth"]
LANES_PER_QUAD = 8

@dataclass
class Lane:
    id: str
    queue: Deque[dict] = field(default_factory=deque)

@dataclass
class Quadrant:
    name: str
    lanes: List[Lane]
    priority: float = 1.0
    mass_share: float = 0.25
    rr_idx: int = 0

class OctupQuadEngine:
    def __init__(self):
        self.tick = 0
        self.angle = 0.0
        self.quads: Dict[str, Quadrant] = {}
        for q in QUADRANTS:
            lanes = [Lane(id=f"{q[:1]}{i}") for i in range(LANES_PER_QUAD)]
            self.quads[q] = Quadrant(name=q, lanes=lanes)
        # Priorities
        self.quads["Revenue"].priority = 1.25
        self.quads["Growth"].priority  = 1.10
        self.quads["Cost"].priority    = 0.95
        self.quads["Overhead"].priority= 0.80

    def _weights(self) -> List[float]:
        r = SQRT_RATIO
        w = [r, 1/r, r/2, 1/(2*r)]
        s = sum(w)
        return [wi/s for wi in w]

    def enqueue(self, quadrant: str, item: dict, lane_hint: int|None=None):
        q = self.quads[quadrant]
        if lane_hint is None:
            tgt = min(q.lanes, key=lambda L: len(L.queue))
        else:
            tgt = q.lanes[lane_hint % LANES_PER_QUAD]
        tgt.queue.append(item)

    def snapshot_load(self) -> Dict[str,int]:
        return {q: sum(len(L.queue) for L in self.quads[q].lanes) for q in QUADRANTS}

    def step(self, raw_mass: float) -> Dict:
        self.tick += 1
        # refresh mass shares
        weights = self._weights()
        for name,w in zip(QUADRANTS,weights):
            self.quads[name].mass_share = w
        # rotation
        self.angle = (self.angle + CAP_ROTATE_DEGREES*(TICK_MULTIPLE)) % 360
        gate = 0.5*(1+math.cos(math.radians(self.angle)))
        rot_mod = max(0.05, gate*(1.0-(TICK_MULTIPLE*0.5)))

        quad_caps = {}
        for q in QUADRANTS:
            base = LANES_PER_QUAD*self.quads[q].mass_share*self.quads[q].priority*rot_mod
            quad_caps[q] = max(0.5, base)

        schedule: List[Tuple[str,str,dict]] = []
        for q in QUADRANTS:
            cap = quad_caps[q]
            qd = self.quads[q]
            pulled = 0.0
            lane_indices = list(range(LANES_PER_QUAD))
            start = qd.rr_idx % LANES_PER_QUAD
            lane_indices = lane_indices[start:] + lane_indices[:start]
            for idx in lane_indices:
                if pulled >= cap: break
                L = qd.lanes[idx]
                if not L.queue: continue
                item = L.queue[0]
                w = float(item.get("weight",1.0))
                if pulled + w <= cap:
                    schedule.append((q,L.id,L.queue.popleft()))
                    pulled += w
            qd.rr_idx = (start+1)%LANES_PER_QUAD

        result = {
            "tick": self.tick,
            "angle_deg": round(self.angle,4),
            "rot_mod": round(rot_mod,6),
            "quad_caps": {k:round(v,3) for k,v in quad_caps.items()},
            "scheduled": [(q,lid,it["id"]) for (q,lid,it) in schedule],
            "backlog": self.snapshot_load()
        }
        # 🔑 Seal it
        result["seal"] = quma_seal(result)
        return result

# --- Demo run ---
if __name__ == "__main__":
    eng = OctupQuadEngine()
    for i in range(10): eng.enqueue("Cost", {"id":f"c{i}","weight":1})
    for i in range(10): eng.enqueue("Revenue", {"id":f"r{i}","weight":1})
    for _ in range(3):
        out = eng.step(raw_mass=1000.0)
        print(out)