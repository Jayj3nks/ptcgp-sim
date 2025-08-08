
from __future__ import annotations
from typing import List, Dict
from collections import Counter

def cost_satisfied(attached: List[str], cost: List[str]) -> bool:
    """Return True if attached energy satisfies cost (typed + colorless)."""
    if not cost:
        return True
    need = Counter(cost)
    att = Counter(attached)
    # Pay typed first
    for t, cnt in list(need.items()):
        if t == "Colorless": 
            continue
        use = min(att.get(t,0), cnt)
        need[t] -= use
        att[t] -= use
        if need[t] > 0:
            return False
    # Pay colorless with anything remaining
    c_need = need.get("Colorless", 0)
    total_att = sum(att.values())
    return total_att >= c_need
