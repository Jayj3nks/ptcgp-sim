# ptcgp_sim/ptcgp_sim/cli.py
from __future__ import annotations

import os
import json
import typer
from rich import print as rprint

from .simulator import Simulator, MatchConfig
from .policy_baseline import baseline_policy
from .types import Phase

# variant-aware + IO helpers
from .card_db import default_card_db_path
from .deckio import normalize_deck_dict, validate_deck as _validate_deck
from .meta_runner import run_meta as _run_meta

app = typer.Typer(help="PTCGP simulator CLI")


# ----------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------
def _rules_path() -> str:
    """Absolute path to rules.json that ships with the package."""
    return os.path.join(os.path.dirname(__file__), "rules.json")


def _card_db_path() -> str:
    """
    Prefer variant-aware merged DB if present; fall back automatically.
    """
    return default_card_db_path()


def _play_match(sim: Simulator, cfg: MatchConfig):
    """
    Run a single match to completion using the baseline policy.
    Returns the terminal state.
    """
    state = sim.reset(cfg)
    while not state.terminal:
        if state.phase == Phase.Main:
            act = baseline_policy(sim, state)
            state = sim.step(state, act)
        else:
            state = sim.step(state, {"type": "Pass"})
    return state


# ----------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------
@app.command()
def demo(seed: int = 123):
    """
    Tiny smoke test using placeholder cards (replace these with real ones for local sanity checks).
    """
    sim = Simulator(_rules_path(), _card_db_path())
    cfg = MatchConfig(
        p0_deck={"Eevee": 10, "Pikachu?": 10},
        p0_energy_types=["Water", "Lightning"],
        p1_deck={"Eevee": 10, "Farfetch'd": 10},
        p1_energy_types=["Colorless"],
        seed=seed,
    )
    state = _play_match(sim, cfg)
    rprint(
        {
            "winner": state.winner,
            "p0_points": state.players[0].prize_points,
            "p1_points": state.players[1].prize_points,
        }
    )


@app.command("run-matches")
def run_matches(
    deck_a: str,
    deck_b: str,
    games: int = 100,
    seed: int = 42,
    out: str = "results.json",
):
    """
    Run A vs B for N games.

    Deck files are JSON like:
    {
      "cards": { "Name [SET]": count, ... },
      "energy_types": ["Fire", "Darkness"]
    }
    (Plain names are accepted but may be ambiguous; they'll be normalized.)
    """
    sim = Simulator(_rules_path(), _card_db_path())

    with open(deck_a, "r", encoding="utf-8-sig") as f:
        da_raw = json.load(f)
    with open(deck_b, "r", encoding="utf-8-sig") as f:
        db_raw = json.load(f)

    # normalize to variant-aware IDs
    da_cards, wa = normalize_deck_dict(da_raw.get("cards", {}))
    db_cards, wb = normalize_deck_dict(db_raw.get("cards", {}))
    if wa:
        rprint({"deck_a_warnings": wa})
    if wb:
        rprint({"deck_b_warnings": wb})

    # HARD VALIDATION (20 cards total + max 2 per line; ex is a separate line)
    ok_a, msgs_a = _validate_deck(da_cards, da_raw.get("energy_types", []))
    ok_b, msgs_b = _validate_deck(db_cards, db_raw.get("energy_types", []))
    if not ok_a or not ok_b:
        rprint({"valid": False, "deck_a_errors": msgs_a, "deck_b_errors": msgs_b})
        raise typer.Exit(code=2)

    wins_a = 0
    for i in range(games):
        cfg = MatchConfig(
            p0_deck=da_cards,
            p0_energy_types=da_raw.get("energy_types", []),
            p1_deck=db_cards,
            p1_energy_types=db_raw.get("energy_types", []),
            seed=seed + i,
        )
        state = _play_match(sim, cfg)
        if state.winner == 0:
            wins_a += 1

    results = {
        "games": games,
        "deck_a_wins": wins_a,
        "deck_b_wins": games - wins_a,
        "win_rate_a": wins_a / games if games else 0.0,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    rprint(results)


@app.command("validate-deck")
def validate_deck(deck_file: str, energy_types: str):
    """
    Validate a single deck JSON and show the normalized (variant-aware) list.

    Usage:
      ptcgp validate-deck my_deck.json "Fire,Darkness"

    Notes:
      • Deck size is enforced at 20 cards.
      • Max 2 copies per specific card line.
      • 'ex' cards are treated as a separate line from non-ex (e.g., 2×Eevee and 2×Eevee ex are allowed).
    """
    with open(deck_file, "r", encoding="utf-8-sig") as f:
        src = json.load(f)

    cards, warns = normalize_deck_dict(src.get("cards", {}))
    energies = [e.strip() for e in energy_types.split(",") if e.strip()]
    ok, msgs = _validate_deck(cards, energies)
    rprint(
        {
            "normalized_cards": cards,
            "warnings": warns,
            "valid": ok,
            "messages": msgs,
        }
    )
    if not ok:
        raise typer.Exit(code=2)


@app.command("normalize-deck")
def normalize_deck(in_file: str, out_file: str):
    """
    Rewrite a deck file so card keys use 'Name [SET]' IDs.
    """
    with open(in_file, "r", encoding="utf-8-sig") as f:
        src = json.load(f)
    cards, warns = normalize_deck_dict(src.get("cards", {}))
    dst = {"cards": cards, "energy_types": src.get("energy_types", [])}
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(dst, f, indent=2)
    rprint({"warnings": warns, "out": out_file})


@app.command("run-meta")
def run_meta(meta_file: str, games: int = 200, seed: int = 42, skip_validate: bool = False):
    """
    Round-robin all decks in a meta file and print win rates.

    By default, all decks are validated (20 cards, max 2 per line, ex split).
    Pass --skip-validate to bypass validation.
    """
    # Validate every deck first (unless skipped)
    if not skip_validate:
        with open(meta_file, "r", encoding="utf-8-sig") as f:
            meta = json.load(f)
        all_ok = True
        problems = {}
        for name, entry in meta.items():
            cards, _ = normalize_deck_dict(entry.get("cards", {}))
            ok, msgs = _validate_deck(cards, entry.get("energy_types", []))
            if not ok:
                all_ok = False
                problems[name] = msgs
        if not all_ok:
            rprint({"valid": False, "errors": problems})
            raise typer.Exit(code=2)

    res = _run_meta(meta_file, games=games, seed=seed)
    rprint(res)


if __name__ == "__main__":
    app()
