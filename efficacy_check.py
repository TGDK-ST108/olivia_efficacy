#!/usr/bin/env python3
import numpy as np

def efficacy_check(ratios):
    """
    ratios: list of (numerator, denominator) pairs
    returns efficacy score [0,1] plus diagnostics
    """
    values = [num/den if den != 0 else 0 for num, den in ratios]
    arr = np.array(values)

    mean = np.mean(arr)
    std = np.std(arr)
    entropy = -np.sum((arr/arr.sum()) * np.log2(arr/arr.sum()+1e-9))

    balance = 1 / (1 + std)       # lower spread = higher balance
    entropy_norm = entropy / np.log2(len(arr))
    dispersion = 1 / (1 + (arr.max() - arr.min()))

    efficacy = (balance + entropy_norm + dispersion) / 3

    return {
        "efficacy_score": round(efficacy, 4),
        "balance": round(balance, 4),
        "entropy": round(entropy_norm, 4),
        "dispersion": round(dispersion, 4),
        "force_rating": int(efficacy * 10000)
    }

# Example:
ratios = [(1,2),(2,3),(3,4),(5,6)]
print(efficacy_check(ratios))