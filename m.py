#!/usr/bin/env python3
# Chamber-Shift Spiral Seal
# 8 duocoupling rounds × 9 vectors → delta-lineate to 21-valley spiral,
# with M-chamber cycling of parameters to avoid mode-locking.
# No external deps.

import math
from dataclasses import dataclass, asdict
from typing import List, Dict

# ---------- Core metrics from one (static) configuration ----------
def _spiral_metrics(g=0.92, lam=0.06, noise=0.08, curvature=1.2,
                    valleys=21, rounds=8, vectors=9, phase=0.0):
    S = math.lcm(rounds, vectors)                 # 72
    geff = g * (1 - lam)                          # per-round effective gain
    total_gain = geff ** rounds                    # after 8 rounds
    stab_margin = 1.0 - geff                       # >0 ⇒ stable
    # Phase contributes to separation (precession improves distinctness slightly)
    phase_bonus = 0.04 * math.cos(phase) + 0.04    # 0..0.08 window
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
        "micro_basins": S * valleys,
        "phase": round(phase, 4)
    }

# ---------- Chamber model ----------
@dataclass
class Chamber:
    name: str
    g: float          # coupling gain per round
    lam: float        # damping
    noise: float      # noise level
    curvature: float  # valley sharpness
    phase_step: float # radians to advance when entering this chamber

def run_chamber_shift_cycle(chambers: List[Chamber],
                            rounds=8, vectors=9, valleys=21,
                            base_phase=0.0, cycles=3) -> Dict:
    """
    Execute M-chamber cycle for `cycles` iterations.
    Returns per-chamber metrics and aggregate two-lens metScore.
    """
    phase = base_phase
    per = []
    agg_score = 0.0
    agg_stab = 0.0
    agg_valcap = 0.0
    agg_lsep = 0.0
    count = 0

    for c_index in range(cycles):
        for ch in chambers:
            metrics = _spiral_metrics(
                g=ch.g, lam=ch.lam, noise=ch.noise, curvature=ch.curvature,
                valleys=valleys, rounds=rounds, vectors=vectors, phase=phase
            )
            per.append({
                "cycle": c_index+1,
                "chamber": ch.name,
                **metrics
            })
            # Aggregate
            agg_score += metrics["efficacy_norm"]
            agg_stab  += metrics["stab_margin"]
            agg_valcap+= metrics["valley_capture"]
            agg_lsep  += metrics["lattice_sep"]
            count += 1
            # advance phase
            phase = (phase + ch.phase_step) % (2*math.pi)

    # Averages
    eff = agg_score / max(1, count)
    met_expanded = int(round(10000 + 15000 * eff))
    return {
        "config": {
            "rounds": rounds, "vectors": vectors, "valleys": valleys,
            "chambers": [asdict(c) for c in chambers],
            "cycles": cycles
        },
        "aggregate": {
            "efficacy_norm": round(eff, 4),
            "metScore_norm_0to1": round(eff, 4),
            "metScore_expanded_10k+": met_expanded,
            "avg_stability_margin": round(agg_stab/max(1, count), 4),
            "avg_valley_capture": round(agg_valcap/max(1, count), 4),
            "avg_lattice_sep": round(agg_lsep/max(1, count), 4),
            "micro_basins_per_cycle": math.lcm(rounds, vectors) * valleys  # 72*21=1512
        },
        "per_chamber": per
    }

# ---------- Reference profiles ----------
def default_4ch_profile():
    # 4-chamber cycle tuned for boundedness with mild precession.
    # Feel free to tweak g/lam/noise/curvature per your environment.
    return [
        Chamber("Intake",      g=0.90, lam=0.06, noise=0.08, curvature=1.15, phase_step=+0.15),
        Chamber("Compression", g=0.93, lam=0.07, noise=0.07, curvature=1.25, phase_step=+0.20),
        Chamber("Ignition",    g=0.95, lam=0.09, noise=0.09, curvature=1.35, phase_step=+0.35),
        Chamber("Exhaust",     g=0.88, lam=0.05, noise=0.07, curvature=1.10, phase_step=+0.10),
    ]

def quiet_6ch_profile():
    # Quieter, higher-damping six-chamber for hostile/noisy fields.
    return [
        Chamber("C1", 0.89, 0.08, 0.10, 1.20, 0.10),
        Chamber("C2", 0.90, 0.09, 0.12, 1.28, 0.15),
        Chamber("C3", 0.91, 0.09, 0.12, 1.34, 0.20),
        Chamber("C4", 0.90, 0.10, 0.14, 1.30, 0.18),
        Chamber("C5", 0.88, 0.08, 0.10, 1.18, 0.12),
        Chamber("C6", 0.87, 0.07, 0.10, 1.16, 0.10),
    ]

# ---------- Demo ----------
if __name__ == "__main__":
    chambers = default_4ch_profile()   # swap to quiet_6ch_profile() if needed
    out = run_chamber_shift_cycle(chambers, rounds=8, vectors=9, valleys=21,
                                  base_phase=0.0, cycles=3)
    from pprint import pprint
    pprint(out["aggregate"])
    # If you want to inspect each chamber step:
    # for row in out["per_chamber"]: pprint(row)