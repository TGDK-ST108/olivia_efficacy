"""
Dzogchen Eye -> Recursive Spiral Honeypot Agent
Implements:
 - Ascending modifier M(x,y,j,r) based on your formula
 - Five-rule recursion (rotation, virtuated collapse, offload/quarantine,
   kerflump entropy compaction, deltaleate -> Quadratalizer)
 - A simple Quadratalizer that maps spiral vectors into a 2x2 "squarefold"
   actionable output.

Notes:
 - This is a simulation/prototype. "plank seconds" are represented as
   simulation ticks (you can map them to real time if desired).
 - Keep tuning knobs at top of file.
"""

import math
import random
import time
from collections import deque, namedtuple

# ---------------------------
# Configuration / Tunables
# ---------------------------
PLANK_TICK_DURATION = 1.0            # simulation: 1 tick = 1 "plank sec" (abstract)
ROTATE_DEGREES = 45.0                # rotate 45 degrees every rotation interval
ROTATE_INTERVAL_TICKS = 15           # rotate every 15 plank ticks
VIRTUATION_THRESHOLD = 0.7           # probability threshold to trigger virtuated collapse
KERFLUMP_ENTROPY_SCALE = 0.08        # scale applied when kerflumping entropy into returns
QUARANTINE_MAX = 200                 # max items to keep in quarantine deck
SPIRAL_STEPS_PER_CYCLE = 8           # spiral nodes per cycle (adjustable)
SEED_HIGGS = 125.10                  # Higgs seed (GeV/c^2) – used as part of modifier
# ---------------------------

# Data structures
Node = namedtuple("Node", ["id", "x", "y", "angle", "radius", "meta"])
QuarantineItem = namedtuple("QuarantineItem", ["node_id", "raw", "clause_vector", "timestamp"])

# Helper math
def radians(d): return d * math.pi / 180.0
def rotate_point(x, y, degrees):
    th = radians(degrees)
    c,s = math.cos(th), math.sin(th)
    return x*c - y*s, x*s + y*c

# ---------------------------
# Core Modifier M(x,y,j,r)
# ---------------------------
def ascending_modifier(xyjr: float) -> float:
    """
    M = xyjr * ( (pi^21 * 7) / (4 * 3 * 13.333) ) * 3^3
    Implemented as a scalar multiplier.
    """
    numerator = (math.pi ** 21) * 7.0
    denominator = 4.0 * 3.0 * 13.333
    factor = (numerator / denominator) * (3 ** 3)  # 3^3 = 27
    return xyjr * factor

# ---------------------------
# Kerflump (entropy compaction)
# ---------------------------
def kerflump_compact(value_vector, entropy_scale=KERFLUMP_ENTROPY_SCALE):
    """
    Injects non-deterministic entropy back into the return stream,
    then compacts (here: compressively folds) the vector magnitude.
    """
    x,y = value_vector
    # small entropy perturbation
    ex = random.gauss(0, entropy_scale)
    ey = random.gauss(0, entropy_scale)
    xp, yp = x + ex, y + ey

    # "Compaction" transform: dampen magnitudes while retaining direction
    mag = math.hypot(xp, yp)
    if mag == 0:
        return (0.0, 0.0)
    compact_mag = math.log1p(mag)  # compressive mapping
    nx = (xp / mag) * compact_mag
    ny = (yp / mag) * compact_mag
    return (nx, ny)

# ---------------------------
# Quadratalizer (Deltaleate)
# ---------------------------
class Quadratalizer:
    """
    Maps a spiral node/vector into a simple 2x2 quadratal (square) result.
    The output is a dict with four quadrants each receiving a score/value.
    """

    def __init__(self, grid_size=2):
        self.grid_size = grid_size

    def quadratalize(self, x, y, angle, radius, meta=None):
        """
        Simple strategy:
         - Compute base energy from radius and angle
         - Distribute energy into 4 quadrants based on rotated angle sectors
        """
        energy = math.hypot(x, y) + (radius * 0.5)
        # Normalize angle 0..360
        a = (angle % 360.0)
        # Determine quadrant mapping: 0-90 -> Q0, 90-180 -> Q1, etc.
        q_index = int(a // 90.0) % 4
        # seed four quadrant scores
        base_scores = [0.0, 0.0, 0.0, 0.0]
        base_scores[q_index] = energy
        # spread residual energy to neighbors to create smoothness
        base_scores[(q_index+1)%4] += energy * 0.25
        base_scores[(q_index-1)%4] += energy * 0.125
        # normalize and return dict
        total = sum(base_scores) or 1.0
        quad = {
            'Q0': base_scores[0]/total,
            'Q1': base_scores[1]/total,
            'Q2': base_scores[2]/total,
            'Q3': base_scores[3]/total,
        }
        # attach mini-metadata fold
        quad['meta'] = {'angle_sector': q_index, 'radius': radius, 'raw_energy': energy}
        return quad

# ---------------------------
# DzogchenEye Agent
# ---------------------------
class DzogchenEye:
    def __init__(self, seed=SEED_HIGGS):
        self.seed = seed
        self.nodes = []
        self.node_counter = 0
        self.rotation = 0.0              # current global rotation (degrees)
        self.tick = 0
        self.quarantine = deque(maxlen=QUARANTINE_MAX)
        self.quadratalizer = Quadratalizer()
        self.spiral_base_radius = 0.02   # base radius for spiral nodes

    def spawn_spiral_nodes(self, steps=SPIRAL_STEPS_PER_CYCLE):
        """
        Create a ring of spiral nodes anchored by the nucleus.
        Each node has radius scaled by ascending modifier.
        """
        nodes = []
        for s in range(steps):
            angle = (360.0 / steps) * s + self.rotation
            # radial growth using phi exponent (toy)
            radius = self.spiral_base_radius * ((1.61803398875) ** (s / steps))
            # XY coords from angle + radius
            x = radius * math.cos(radians(angle))
            y = radius * math.sin(radians(angle))
            node = Node(id=self.node_counter, x=x, y=y, angle=angle, radius=radius, meta={})
            self.nodes.append(node)
            nodes.append(node)
            self.node_counter += 1
        return nodes

    def rotate_rule(self):
        """Rotate by ROTATE_DEGREES."""
        self.rotation = (self.rotation + ROTATE_DEGREES) % 360.0

    def virtuated_collapse(self, node: Node) -> bool:
        """
        Collapse snapshot if analysis yields a 'positive' result.
        We simulate analysis by probabilistic check weighted by node radius and seed.
        """
        # a pseudo-evidence score combining radius, seed randomness, and node angle variance
        evidence = math.tanh(node.radius * (self.seed / 100.0)) + random.random() * 0.2
        positive = evidence > VIRTUATION_THRESHOLD
        return positive

    def offload_rule(self, node: Node, clause_vector):
        """Offload raw captured signal into quarantine deck with clause metadata."""
        ts = time.time()
        raw_capture = {'x': node.x, 'y': node.y, 'angle': node.angle, 'radius': node.radius}
        qi = QuarantineItem(node_id=node.id, raw=raw_capture, clause_vector=clause_vector, timestamp=ts)
        self.quarantine.append(qi)
        return qi

    def kerflump_rule(self, vec):
        """Apply kerflump entropy + compaction to a vector (x,y)."""
        return kerflump_compact(vec, entropy_scale=KERFLUMP_ENTROPY_SCALE)

    def deltaleate_rule(self, node: Node, vec):
        """Run Quadratalizer on the (possibly kerflumped) vector."""
        x,y = vec
        quad = self.quadratalizer.quadratalize(x, y, node.angle, node.radius, meta=node.meta)
        return quad

    def run_cycle(self):
        """
        One analysis cycle for the agent:
         - Spawn nodes
         - For each node: analyze (virtuated collapse), possibly collapse+offload,
           apply kerflump, quadratalize, and emit the quadratal output.
         - Apply rotation rule occasionally
        """
        self.tick += 1
        nodes = self.spawn_spiral_nodes()

        outputs = []
        for node in nodes:
            # 1) Analysis stage
            positive = self.virtuated_collapse(node)

            if positive:
                # 2) collapse -> snapshot (we'll construct a clause_vector)
                # build base clause vector using ascending modifier seeded by node id/seed
                base_seed = float(node.id % 1000) + (self.seed * 0.01)
                modifier_scalar = ascending_modifier(base_seed)
                clause_vector = (node.x * modifier_scalar, node.y * modifier_scalar)

                # 3) offload raw capture to quarantine (with clause_vector reference)
                qi = self.offload_rule(node, clause_vector)

                # 4) kerflump entropy compaction
                compacted = self.kerflump_rule(clause_vector)

                # 5) deltaleate -> quadratalizer
                quad = self.deltaleate_rule(node, compacted)

                # put final output
                outputs.append({'node': node.id, 'quadratal': quad, 'quarantine_ref': qi})

            else:
                # Not positive -> still apply kerflump for deceptive returns and a soft quadratalize
                benign_vec = (node.x * 0.5, node.y * 0.5)
                compacted = self.kerflump_rule(benign_vec)
                quad = self.deltaleate_rule(node, compacted)
                outputs.append({'node': node.id, 'quadratal': quad, 'quarantine_ref': None})

        # Rotation rule: every ROTATE_INTERVAL_TICKS, rotate by ROTATE_DEGREES
        if (self.tick % ROTATE_INTERVAL_TICKS) == 0:
            self.rotate_rule()

        return outputs

# ---------------------------
# Example: run a few cycles
# ---------------------------
if __name__ == "__main__":
    agent = DzogchenEye()
    cycles = 6
    for c in range(cycles):
        out = agent.run_cycle()
        print(f"=== Cycle {c+1} (tick {agent.tick}) -> nodes produced: {len(agent.nodes)} ===")
        # print a short summary for the first three node outputs
        for item in out[:3]:
            nid = item['node']
            quad = item['quadratal']
            qref = item['quarantine_ref']
            qinfo = f"QRef(node={qref.node_id})" if qref else "no-quarantine"
            print(f" node {nid}: sector={quad['meta']['angle_sector']}, scores={{Q0:{quad['Q0']:.3f},Q1:{quad['Q1']:.3f},Q2:{quad['Q2']:.3f},Q3:{quad['Q3']:.3f}}} -> {qinfo}")
        print(f" quarantine size: {len(agent.quarantine)}")
        # advance simulation quickly (no sleep necessary in prototype)