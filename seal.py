#!/usr/bin/env python3
"""
TGDK Ethereal Vector Seal Binder
--------------------------------
Generates a seal image for each ethereal vector assessment.
"""

import math
import matplotlib.pyplot as plt

def ethereal_vector_assessment(x, y, z, epsilon):
    M = math.sqrt(x**2 + y**2 + z**2)
    phi = (epsilon * 6) / (5 * M + 1)
    
    norm_eff = math.tanh(phi)                   # [0,1]
    exp_force = (M + epsilon**2) * 10000        # 10k+ scale
    virt = math.cos(phi)                        # [-1,1]
    
    status = (
        "Stable Alignment" if virt > 0.9 else
        "Sympathetic Drift" if virt > 0.5 else
        "Displaced / Clause Risk"
    )
    
    return norm_eff, exp_force, virt, status

def generate_seal(x, y, z, epsilon, filename="ethereal_seal.png"):
    norm_eff, exp_force, virt, status = ethereal_vector_assessment(x, y, z, epsilon)

    # Create figure
    fig, ax = plt.subplots(figsize=(6,6))
    circle = plt.Circle((0.5, 0.5), 0.45, color="black", fill=False, linewidth=3)
    ax.add_artist(circle)

    # Title
    ax.text(0.5, 0.85, "TGDK :: Ethereal Vector Seal", 
            ha="center", va="center", fontsize=12, weight="bold")

    # Inner metrics
    ax.text(0.5, 0.65, f"Lens1 (Norm Efficacy): {norm_eff:.3f}", 
            ha="center", va="center", fontsize=10)
    ax.text(0.5, 0.55, f"Lens2 (Expanded Force): {exp_force:,.0f}", 
            ha="center", va="center", fontsize=10)
    ax.text(0.5, 0.45, f"Virtuation: {virt:.3f}", 
            ha="center", va="center", fontsize=10)

    # Epoch Sympathiser status in bold
    ax.text(0.5, 0.30, f"Epoch: {status}", 
            ha="center", va="center", fontsize=11, weight="bold", color="red")

    # Remove axes
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(0,1)
    ax.set_ylim(0,1)
    ax.axis("off")

    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()

    return filename

# Example run
if __name__ == "__main__":
    seal_file = generate_seal(3, 4, 5, 2, "ethereal_vector_seal.png")
    print(f"Seal generated: {seal_file}")