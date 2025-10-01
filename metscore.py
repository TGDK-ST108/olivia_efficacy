# metScore dual-lens verifier
D_min, D_max = 86, 410  # campaign bounds

# Replace these with your actual campaign samples:
digits = [86, 117, 159, 243, 410]
phi    = [0.602, 0.157, 0.494, 0.887, 0.205]  # approximations used above

def eff_norm(D):
    return (D - D_min) / (D_max - D_min)

def force(D, ph):
    return 10_000 * D + int(1_000_000 * ph)

rows = []
for t, (D, ph) in enumerate(zip(digits, phi)):
    rows.append((t, D, ph, round(eff_norm(D), 3), force(D, ph)))

print("t | D |   phi   | eff_norm |   force")
print("--+---+---------+----------+---------")
for t, D, ph, en, F in rows:
    print(f"{t:1d} |{D:3d}| {ph:7.3f} | {en:8.3f} | {F:9,d}")

# Snapshot (last step)
t, D, ph, en, F = rows[-1]
print("\nSnapshot metScore:")
print(f"  normalized = {en:.3f}")
print(f"  expanded   = {F:,d}")