#!/usr/bin/env python3
# High-Capture Matrix, Stabilized (HCMS)
# 8 duocoupling rounds × 9 vectors → 21-valley spiral with chamber-shift cycling.
# Focus: maximize valley capture (curvature) while keeping bounded stability.

import math
from dataclasses import dataclass, asdict
from typing import List, Dict

def _spiral_metrics(g=0.92, lam=0.06, noise=0.08, curvature=1.2,
                    valleys=21, rounds=8, vectors=9, phase=0.0):
    S = math.lcm(rounds, vectors)        # 72
    geff = g * (1 - lam)                 # per-round effective gain
    total_gain = geff ** rounds
    stab_margin = 1.0 - geff             # >0 ⇒ stable
    # small precession assist to separation
    phase_bonus = 0.04 * math.cos(phase) + 0.04
    valley_capture = 1 / (1 + math.exp(-(curvature * total_gain - 0.8*noise - 0.2)))
    lattice_sep = max(0.0, min(1.0, (S/(S+9)) * (1 - noise) * (0.5 + 0.5*total_gain) + phase_bonus))
    efficacy = 0.45*valley_capture + 0.35*lattice_sep + 0.20*max(0.0, stab_margin)
    met_norm = max(0.0, min(1.0, efficacy))
    met_expanded = int(round(10000 + 15000 * met_norm))
    return {
        "symmetry_S": S,
        "stab_margin": round(stab_margin, 4),
        "valley_capture": round(valley_capture, 4),
        "lattice_sep": round(lattice_sep, 4),
        "efficacy_norm": round(met_norm, 4),
        "metScore_norm_0to1": round(met_norm, 4),
        "metScore_expanded_10k+": met_expanded,
        "micro_basins": S * valleys,      # 72 × 21 = 1512
        "phase": round(phase, 4)
    }

@dataclass
class Chamber:
    name: str
    g: float          # coupling gain per round
    lam: float        # damping
    noise: float      # noise level
    curvature: float  # valley sharpness
    phase_step: float # radians to advance entering this chamber

def run_chamber_shift_cycle(chambers: List[Chamber],
                            rounds=8, vectors=9, valleys=21,
                            base_phase=0.0, cycles=3) -> Dict:
    phase = base_phase
    per, agg = [], {"eff":0,"stab":0,"vc":0,"ls":0,"n":0}
    for c in range(cycles):
        for ch in chambers:
            m = _spiral_metrics(ch.g, ch.lam, ch.noise, ch.curvature,
                                valleys, rounds, vectors, phase)
            per.append({"cycle": c+1, "chamber": ch.name, **m})
            agg["eff"] += m["efficacy_norm"]; agg["stab"] += m["stab_margin"]
            agg["vc"]  += m["valley_capture"]; agg["ls"]   += m["lattice_sep"]; agg["n"] += 1
            phase = (phase + ch.phase_step) % (2*math.pi)
    avg_eff = agg["eff"]/agg["n"]
    return {
        "config": {"rounds": rounds, "vectors": vectors, "valleys": valleys,
                   "chambers": [asdict(x) for x in chambers], "cycles": cycles},
        "aggregate": {
            "efficacy_norm": round(avg_eff, 4),
            "metScore_norm_0to1": round(avg_eff, 4),
            "metScore_expanded_10k+": int(round(10000 + 15000*avg_eff)),
            "avg_stability_margin": round(agg["stab"]/agg["n"], 4),
            "avg_valley_capture": round(agg["vc"]/agg["n"], 4),
            "avg_lattice_sep": round(agg["ls"]/agg["n"], 4),
            "micro_basins_per_cycle": math.lcm(rounds, vectors) * valleys
        },
        "per_chamber": per
    }

# -------- HCMS 5-chamber profile --------
# Higher capture via curvature in two central chambers; bounded geff in all.
def HCMS_profile():
    #               name           g     lam   noise curvature phase_step
    return [
        Chamber("Intake",          0.91, 0.06, 0.08, 1.25,     0.17),
        Chamber("Alignment",       0.93, 0.07, 0.08, 1.35,     0.19),
        Chamber("Capture-1",       0.96, 0.10, 0.09, 1.50,     0.31),  # high curvature
        Chamber("Capture-2",       0.95, 0.09, 0.09, 1.45,     0.23),  # sustain
        Chamber("Cooldown",        0.89, 0.06, 0.08, 1.20,     0.11),
    ]

# Safety guardrails: keep geff < 0.98 in all chambers
def validate_profile(chambers: List[Chamber]):
    for ch in chambers:
        geff = ch.g * (1 - ch.lam)
        assert geff < 0.98, f"{ch.name} too hot: geff={geff:.3f}"

if __name__ == "__main__":
    prof = HCMS_profile()
    validate_profile(prof)
    out = run_chamber_shift_cycle(prof, rounds=8, vectors=9, valleys=21,
                                  base_phase=0.0, cycles=3)
    from pprint import pprint
    pprint(out["aggregate"])
    # Inspect steps if needed:
    # for row in out["per_chamber"]: pprint(row)