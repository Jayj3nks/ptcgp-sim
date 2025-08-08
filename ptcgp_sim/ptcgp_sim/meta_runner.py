
from __future__ import annotations
import json, os
from typing import Dict, Any
from .simulator import Simulator, MatchConfig
from .types import Phase
from .deckio import normalize_deck_dict

def play_match(sim: Simulator, deck_a: Dict[str,int], et_a, deck_b: Dict[str,int], et_b, seed: int) -> int | None:
    cfg = MatchConfig(
        p0_deck=deck_a,
        p0_energy_types=et_a,
        p1_deck=deck_b,
        p1_energy_types=et_b,
        seed=seed
    )
    state = sim.reset(cfg)
    from .policy_baseline import baseline_policy
    while not state.terminal:
        if state.phase == Phase.Main:
            act = baseline_policy(sim, state)
            state = sim.step(state, act)
        else:
            state = sim.step(state, {"type": "Pass"})
    return state.winner

def run_meta(meta_file: str, games: int = 200, seed: int = 42, rules_path: str | None = None, card_db_path: str | None = None) -> Dict[str, Any]:
    if rules_path is None:
        rules_path = os.path.join(os.path.dirname(__file__), "rules.json")
    sim = Simulator(rules_path, card_db_path)

    meta = json.load(open(meta_file, "r"))
    names = list(meta.keys())
    results: Dict[str, Dict[str, float]] = {n: {} for n in names}

    norm: Dict[str, Dict[str,int]] = {}
    energies: Dict[str, list] = {}
    for name, d in meta.items():
        cards, warns = normalize_deck_dict(d["cards"])
        if warns:
            print(f"[warn] {name}: \n  - " + "\n  - ".join(warns))
        norm[name] = cards
        energies[name] = d.get("energy_types", [])

    for i, a in enumerate(names):
        for j, b in enumerate(names):
            if i >= j:
                continue
            wins_a = 0
            for g in range(games):
                w = play_match(sim, norm[a], energies[a], norm[b], energies[b], seed + g)
                if w == 0: wins_a += 1
            wr_a = wins_a / games
            results[a][b] = wr_a
            results[b][a] = 1 - wr_a
            print(f"{a} vs {b}: {wr_a:.3f}")
    return results
