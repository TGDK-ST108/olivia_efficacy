import math
import random
import time
import hashlib
import json

# ---------- utilities ----------
def normalize(vec):
    s = sum(abs(v) for v in vec) or 1.0
    return tuple(v / s for v in vec)

# QUMA nonstandard hex serializer (simple deterministic transform + salt)
QUMA_MAP = {
    '0':'Q','1':'X','2':'M','3':'H','4':'A','5':'V','6':'E','7':'R','8':'S','9':'O',
    'a':'L','b':'I','c':'G','d':'T','e':'U','f':'N'
}
def quma_serialize(obj, salt="QUMA"):
    """
    Deterministic quma serialize: JSON -> sha256 -> map hex -> QUMA string.
    Use to create 'sealed' blob that won't be standard hex.
    """
    j = json.dumps(obj, sort_keys=True, separators=(',',':'))
    h = hashlib.sha256((j + salt).encode()).hexdigest()
    return ''.join(QUMA_MAP[ch] for ch in h)

# Assume Quadratalizer exists (from earlier) with .quadratalize(x,y,angle,radius,meta)
# For this snippet, implement a compact version:
class SimpleQuadratalizer:
    def quadratalize(self, x, y, angle, radius, meta=None):
        energy = math.hypot(x, y) + (radius * 0.5)
        a = (angle % 360.0)
        idx = int(a // 90.0) % 4
        scores = [0.0,0.0,0.0,0.0]
        scores[idx] = energy
        scores[(idx+1)%4] += energy*0.3
        scores[(idx-1)%4] += energy*0.15
        total = sum(scores) or 1.0
        quad = {'Q0':scores[0]/total,'Q1':scores[1]/total,'Q2':scores[2]/total,'Q3':scores[3]/total}
        quad['meta'] = {'sector':idx, 'raw_energy':energy}
        return quad

# Kerflump variant that accepts a seed for deterministic-but-obfuscated channeling
def kerflump_channel(x,y,entropy_scale=0.08, seed=None):
    """
    Produce a kerflumped vector variation.
    If seed provided -> deterministic pseudo-random stream (useful for reproducible duo channels).
    """
    rnd = random.Random(seed)
    ex = rnd.gauss(0, entropy_scale)
    ey = rnd.gauss(0, entropy_scale)
    xp, yp = x + ex, y + ey
    mag = math.hypot(xp, yp)
    if mag == 0:
        return (0.0, 0.0)
    compact_mag = math.log1p(mag)
    return ((xp/mag)*compact_mag, (yp/mag)*compact_mag)

# ---------- DuoQuadratlizer ----------
class DuoQuadratlizer:
    def __init__(self, quadratalizer=None):
        self.q = quadratalizer or SimpleQuadratalizer()

    def duoquadratlize_node(self, node, base_seed, metronome_tick):
        """
        node: object with x,y,angle,radius,meta
        base_seed: large int or string to derive channel seeds
        metronome_tick: the SCOOTY tick time (plank-sec)
        """
        # derive two deterministic seeds from base seed + node id + tick
        s1 = hashlib.sha256(f"{base_seed}|{node.id}|{metronome_tick}|A".encode()).hexdigest()
        s2 = hashlib.sha256(f"{base_seed}|{node.id}|{metronome_tick}|B".encode()).hexdigest()
        # convert hex -> int seeds
        seedA = int(s1[:16], 16)
        seedB = int(s2[:16], 16)

        # kerflump into two channels
        vecA = kerflump_channel(node.x, node.y, entropy_scale=0.06, seed=seedA)
        vecB = kerflump_channel(node.x, node.y, entropy_scale=0.12, seed=seedB)

        # quadratalize each channel
        quadA = self.q.quadratalize(vecA[0], vecA[1], node.angle, node.radius, meta=node.meta)
        quadB = self.q.quadratalize(vecB[0], vecB[1], node.angle, node.radius, meta=node.meta)

        # differential analysis
        diffs = {k: quadA[k] - quadB.get(k,0.0) for k in ['Q0','Q1','Q2','Q3']}
        diff_norm = normalize((diffs['Q0'], diffs['Q1'], diffs['Q2'], diffs['Q3']))
        anomaly_score = sum(abs(v) for v in diffs)  # simple L1 anomaly

        # seal both outputs using QUMA serializer
        meta_blob = {
            'node_id': node.id,
            'tick': metronome_tick,
            'angle': node.angle,
            'radius': node.radius,
            'anomaly': anomaly_score
        }
        sealedA = quma_serialize({'quad':quadA, 'meta':meta_blob}, salt="QUMA-A")
        sealedB = quma_serialize({'quad':quadB, 'meta':meta_blob}, salt="QUMA-B")

        # produce final record suitable for quarantine or chain anchoring
        record = {
            'node': node.id,
            'tick': metronome_tick,
            'quadA': quadA,
            'quadB': quadB,
            'diff_normalized': diff_norm,
            'anomaly_score': anomaly_score,
            'sealed_blob_A': sealedA,
            'sealed_blob_B': sealedB,
            'scooty_stamp': f"SCOOTY::{metronome_tick}"
        }
        return record

# ---------- Example usage ----------
# Suppose 'node' follows the Node namedtuple shape from earlier:
from collections import namedtuple
Node = namedtuple("Node", ["id","x","y","angle","radius","meta"])
test_node = Node(42, 0.0123, -0.0067, 37.5, 0.018, {'label':'zero-agent'})

dq = DuoQuadratlizer()
rec = dq.duoquadratlize_node(test_node, base_seed="DZOGCHEN_ZERO", metronome_tick=12345)
print("Node", rec['node'], "anomaly:", rec['anomaly_score'])
print("sealedA (prefix):", rec['sealed_blob_A'][:24])
print("sealedB (prefix):", rec['sealed_blob_B'][:24])