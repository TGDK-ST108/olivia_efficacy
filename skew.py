#!/usr/bin/env python3
import math, numpy as np
from typing import List, Tuple, Literal, Dict

def efficacy_check_from_values(values: List[float]) -> Dict[str, float]:
    arr = np.array(values, dtype=float)
    if len(arr) == 0:
        return {"efficacy_score": 0.0, "balance": 0.0, "entropy": 0.0, "dispersion": 0.0, "force_rating": 0}

    s = arr.sum()
    probs = (np.ones_like(arr)/len(arr)) if s == 0 else (arr/s)

    entropy = -np.sum(probs * np.log2(probs + 1e-9))
    balance = 1.0 / (1.0 + float(arr.std()))
    entropy_norm = float(entropy / math.log2(len(arr)))
    dispersion = 1.0 / (1.0 + (float(arr.max()) - float(arr.min())))
    efficacy = (balance + entropy_norm + dispersion) / 3.0

    return {
        "efficacy_score": round(efficacy, 4),      # [0,1]
        "balance": round(balance, 4),
        "entropy": round(entropy_norm, 4),
        "dispersion": round(dispersion, 4),
        "force_rating": int(round(efficacy * 10000))   # 10k-scale
    }

def efficacy_check(ratios: List[Tuple[float, float]]) -> Dict[str, float]:
    # Convenience wrapper for the non-skewed case
    values = [n/d if d != 0 else 0.0 for n,d in ratios]
    return efficacy_check_from_values(values)

def skew_and_check(
    ratios: List[Tuple[float, float]],
    folds: int = 4,
    dilation: float = 1.15,
    divert: float = 0.15,
    divert_mode: Literal["next", "spread", "matrix"] = "next",
    matrix: np.ndarray = None,
    depth_mode: Literal["by_fold", "by_turn", "hybrid"] = "by_fold",
    preserve_sum: bool = True,
) -> Dict[str, object]:
    """
    Dilated metric fold + diversion, then efficacy check.

    Parameters
    ----------
    ratios: list of (numerator, denominator)
    folds: number of fold partitions
    dilation: per-fold (or per-turn) multiplicative dilation (>1 amplifies later folds)
    divert: fraction of each element diverted away according to divert_mode
    divert_mode:
        - "next": send divert fraction from fold f to fold (f+1) % folds
        - "spread": distribute divert fraction evenly to all other folds
        - "matrix": use a custom (folds x folds) stochastic matrix
    matrix: required when divert_mode == "matrix" (rows ~ source fold, cols ~ target fold)
    depth_mode:
        - "by_fold": power = fold_index
        - "by_turn": power = turn_index (i // folds)
        - "hybrid": power = fold_index + turn_index
    preserve_sum: if True, renormalize post-diversion to original sum of values

    Returns
    -------
    dict with:
      - 'values_raw': base values
      - 'values_dilated': post-dilation
      - 'values_diverted': post-diversion (final)
      - 'diagnostics': efficacy metrics on final values
    """
    # --- 1) Base values
    base = np.array([ (n/d if d != 0 else 0.0) for (n,d) in ratios ], dtype=float)
    if len(base) == 0:
        return {"values_raw": [], "values_dilated": [], "values_diverted": [], "diagnostics": efficacy_check_from_values([])}

    # --- 2) Assign folds / turns
    idx = np.arange(len(base))
    fold_idx = idx % folds
    turn_idx = idx // folds

    # --- 3) Dilation power per element
    if depth_mode == "by_fold":
        power = fold_idx
    elif depth_mode == "by_turn":
        power = turn_idx
    elif depth_mode == "hybrid":
        power = fold_idx + turn_idx
    else:
        raise ValueError("depth_mode must be one of {'by_fold','by_turn','hybrid'}")

    dil_factors = np.power(dilation, power.astype(float))
    dilated = base * dil_factors

    # --- 4) Build diversion plan
    # Compute totals per fold to divert; operate at element level preserving fold mapping.
    final = dilated.copy()
    if divert > 0.0:
        # Aggregate by fold
        fold_sums = np.zeros(folds, dtype=float)
        for f in range(folds):
            fold_sums[f] = float(dilated[fold_idx == f].sum())

        # Outflow per fold
        outflow = divert * fold_sums
        inflow = np.zeros_like(fold_sums)

        if divert_mode == "next":
            for f in range(folds):
                inflow[(f + 1) % folds] += outflow[f]

        elif divert_mode == "spread":
            # Spread to all OTHER folds uniformly
            if folds > 1:
                for f in range(folds):
                    share = outflow[f] / (folds - 1)
                    for g in range(folds):
                        if g != f:
                            inflow[g] += share

        elif divert_mode == "matrix":
            if matrix is None:
                raise ValueError("Provide a (folds x folds) stochastic matrix for divert_mode='matrix'.")
            M = np.array(matrix, dtype=float)
            if M.shape != (folds, folds):
                raise ValueError(f"matrix must be shape ({folds},{folds})")
            # Row-stochastic: each row sums to 1 (how a fold distributes its outflow)
            row_sums = M.sum(axis=1, keepdims=True)
            if not np.allclose(row_sums, 1.0, atol=1e-6):
                raise ValueError("diversion matrix rows must sum to 1")
            inflow = outflow @ M  # shape: (folds,)

        else:
            raise ValueError("divert_mode must be 'next', 'spread', or 'matrix'")

        # Apply outflow and inflow back to elements proportionally within each fold
        # Reduce each element in fold f by the same fraction of its fold outflow
        final = dilated.copy()
        for f in range(folds):
            mask = (fold_idx == f)
            fold_total = float(dilated[mask].sum())
            if fold_total > 0:
                final[mask] *= (1.0 - divert)  # uniform reduction for that fold

        # Distribute inflow into elements of destination folds proportional to their (post-reduction) mass
        for g in range(folds):
            mask = (fold_idx == g)
            seg = final[mask]
            seg_sum = float(seg.sum())
            if inflow[g] > 0 and seg_sum > 0:
                final[mask] += (seg / seg_sum) * inflow[g]
            elif inflow[g] > 0 and seg_sum == 0:
                # if destination fold is empty (edge case), distribute evenly across its members
                count = int(mask.sum())
                if count > 0:
                    final[mask] += inflow[g] / count

        # Optional global renormalization to preserve total sum of the dilated vector
        if preserve_sum:
            target_sum = float(dilated.sum())
            cur_sum = float(final.sum())
            if cur_sum > 0:
                final *= (target_sum / cur_sum)

    diagnostics = efficacy_check_from_values(final.tolist())
    return {
        "values_raw": base.tolist(),
        "values_dilated": dilated.tolist(),
        "values_diverted": final.tolist(),
        "diagnostics": diagnostics
    }

# -------------------------
# Example usage (uncomment to try):
# ratios = [(1,100),(1,10),(10,1),(100,1)]
# out = skew_and_check(
#     ratios,
#     folds=4,
#     dilation=1.25,          # amplify later folds/turns
#     divert=0.20,            # 20% of each fold mass is diverted
#     divert_mode="next",     # push to the next fold cyclically
#     depth_mode="hybrid",    # fold index + turn index
#     preserve_sum=True
# )
# from pprint import pprint; pprint(out)