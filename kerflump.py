import numpy as np, math, random

def kerflump(values, nonlinear="sqrt", jitter=0.05, seed=None):
    """
    Kerflump = collapse & redistribute values chaotically.
    nonlinear: 'sqrt', 'log', 'tanh', or None
    jitter: fraction of value range to add as noise
    """
    rng = np.random.default_rng(seed)
    vals = np.array(values, dtype=float)

    # 1. shuffle
    rng.shuffle(vals)

    # 2. nonlinear transform
    if nonlinear == "sqrt":
        vals = np.sqrt(vals)
    elif nonlinear == "log":
        vals = np.log1p(vals)  # log(1+x) to keep safe
    elif nonlinear == "tanh":
        vals = np.tanh(vals)
    # else: leave as-is

    # 3. jitter
    noise = rng.uniform(-jitter, jitter, size=len(vals))
    vals = vals + noise

    # ensure no negatives
    vals = np.clip(vals, 0, None)

    # 4. renormalize to original sum
    target_sum = np.sum(values)
    cur_sum = np.sum(vals)
    if cur_sum > 0:
        vals = vals * (target_sum / cur_sum)

    return vals.tolist()