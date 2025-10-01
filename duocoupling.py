#!/usr/bin/env python3
# Stash/Spiral Seal – 8×9 duocoupling → 21-valley delta-lineation
# Inputs you should tune: g (coupling gain per round), lam (damping), noise (0..1), curvature (valley sharpness)
import math

def spiral_seal_metrics(g=0.92, lam=0.06, noise=0.08, curvature=1.2, valleys=21, rounds=8, vectors=9):
    S = math.lcm(rounds, vectors)              # symmetry order (72)
    geff = g * (1 - lam)                       # effective per-round gain
    total_gain = geff ** rounds                # after 8 rounds
    # Stability margin: >0 stable, <=0 unstable
    stab_margin = 1.0 - geff                   # keep > 0
    # Valley capture probability: sharper curvature + lower noise + moderate total_gain help
    valley_capture = 1 / (1 + math.exp(-(curvature * total_gain - 0.8*noise - 0.2)))
    # Phase-lattice occupancy (0..1): how well 72 states are distinguished after 9-way spread
    lattice_sep = max(0.0, min(1.0, (S/(S+9)) * (1 - noise) * (0.5 + 0.5*total_gain)))
    # Composite efficacy (0..1)
    efficacy = 0.45*valley_capture + 0.35*lattice_sep + 0.20*max(0.0, stab_margin)
    # Two-lens metScore
    met_norm = max(0.0, min(1.0, efficacy))
    met_expanded = int(round(10000 + 15000 * met_norm))  # 10k floor, ~25k ceiling
    return {
        "symmetry_S": S,
        "stab_margin": round(stab_margin, 4),
        "valley_capture": round(valley_capture, 4),
        "lattice_sep": round(lattice_sep, 4),
        "efficacy_norm": round(met_norm, 4),
        "metScore_norm_0to1": round(met_norm, 4),
        "metScore_expanded_10k+": met_expanded,
        "micro_basins": S * valleys
    }

# example
if __name__ == "__main__":
    print(spiral_seal_metrics(
        g=0.92,      # per-round coupling gain (try 0.88..0.97)
        lam=0.06,    # damping (try 0.04..0.10)
        noise=0.08,  # environment/adversary noise (0..0.3 typical)
        curvature=1.2 # valley sharpness (1.0 flat .. 1.6 sharp)
    ))