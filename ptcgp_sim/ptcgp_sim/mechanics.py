
from __future__ import annotations
from typing import Tuple, List, Dict
import re
from .types import BattleState, PokemonInstance
from .card_db import load_card_db, is_ex_card
from .costs import cost_satisfied
from .rng import RNG

WEAKNESS_BONUS = 20  # Pocket flat bonus

def calc_damage_with_effects(attacker: PokemonInstance, defender: PokemonInstance, attack: dict, rng: RNG) -> Tuple[int, Dict]:
    base = int(attack.get("damage", 0) or 0)
    effect_text = (attack.get("effect") or "").strip()
    info = {}

    # Pattern: "does X more damage for each [T] Energy attached to this Pokémon."
    m = re.search(r"does\s+(\d+)\s+more damage for each \[([A-Z])\]\s+Energy attached to this Pokémon", effect_text, re.I)
    if m:
        bonus_per = int(m.group(1))
        sym = m.group(2)
        type_map = {
            "R":"Fire","W":"Water","G":"Grass","L":"Lightning","P":"Psychic","F":"Fighting","D":"Darkness","M":"Metal","Y":"Fairy","C":"Colorless"
        }
        tname = type_map.get(sym, None)
        if tname:
            count = sum(1 for e in attacker.attached_energy if e == tname)
            base += bonus_per * count
            info["bonus_by_attached"] = (tname, count, bonus_per)

    # Pattern: "Flip N coins. This attack does X damage for each heads."
    m = re.search(r"Flip\s+(\d+)\s+coins?\.\s*This attack does\s+(\d+)\s+damage for each heads", effect_text, re.I)
    if m:
        n = int(m.group(1)); per = int(m.group(2))
        heads = sum(1 for _ in range(n) if rng.randint(0,1)==1)
        base += per * heads
        info["coin_heads"] = heads

    # Pattern: "Flip 2 coins. This attack does 100 damage for each heads." already covered
    # Pattern: "Discard N [T] Energy from this Pokémon."
    m = re.search(r"Discard\s+(\d+)\s+\[([A-Z])\]\s+Energy from this Pokémon", effect_text, re.I)
    if m:
        n = int(m.group(1)); sym = m.group(2)
        type_map = {"R":"Fire","W":"Water","G":"Grass","L":"Lightning","P":"Psychic","F":"Fighting","D":"Darkness","M":"Metal","Y":"Fairy","C":"Colorless"}
        tname = type_map.get(sym, None)
        if tname:
            # mark to discard after damage is applied (Pocket consumes energy only on retreat; here effect forces discard)
            info["discard_after"] = (tname, n)

    # Pattern: "This attack does 50 damage to 1 of your opponent's Pokémon." (sniping) – we simplify to Active for now
    if "50 damage to 1 of your opponent's Pokémon" in effect_text:
        # Could target bench; for stub, keep Active. Leave note.
        info["note"] = "bench_snipe_ignored_stub"

    # Status effects
    if "is now Paralyzed" in effect_text:
        info["apply_status"] = ("Paralyzed", 1)
    if "is now Asleep" in effect_text:
        info["apply_status"] = ("Asleep", 1)
    if "is now Confused" in effect_text:
        info["apply_status"] = ("Confused", 1)

    return base, info

def apply_weakness(dmg: int, attacker_type: str, defender_weakness: str) -> int:
    if defender_weakness and defender_weakness.lower() != "none" and attacker_type == defender_weakness:
        return dmg + WEAKNESS_BONUS
    return dmg

def perform_attack(state: BattleState, attack: dict) -> None:
    # Attacker/Defender
    atk_player = state.players[state.current_player]
    def_player = state.players[1 - state.current_player]
    attacker = atk_player.active
    defender = def_player.active
    assert attacker and defender, "Both players must have an Active Pokémon"

    rng = RNG(state.rng_seed + state.turn*7919 + state.current_player*13)
    # Cost check
    if not cost_satisfied(attacker.attached_energy, attack.get("energy_cost", [])):
        return  # illegal in real sim; here we just no-op

    # Damage & effects
    dmg, info = calc_damage_with_effects(attacker, defender, attack, rng)
    # Weakness
    dmg = apply_weakness(dmg, _card_type(attacker.card_id), _card_weakness(defender.card_id))

    # Apply damage
    defender.hp -= max(0, dmg)

    # Post-attack discards (from effects)
    if "discard_after" in info:
        etype, n = info["discard_after"]
        to_keep = []
        removed = 0
        for e in attacker.attached_energy:
            if e == etype and removed < n:
                removed += 1
            else:
                to_keep.append(e)
        attacker.attached_energy = to_keep

    # Status
    if "apply_status" in info:
        status, _ = info["apply_status"]
        defender.status = status

    # KO check and points
    if defender.hp <= 0:
        def_player.discard.append(defender.card_id)
        def_player.active = None
        # Points awarded based on KO'd card type (ex=2 else 1)
        points = 2 if is_ex_card(defender.card_id) else 1
        atk_player.prize_points += points

def _CARD_DB():
    # Lazy-load the bundled example DB
    import os, json
    here = os.path.dirname(__file__)
    path = os.path.join(here, "card_db_eevee_grove.json")
    if not os.path.exists(path):
        path = os.path.join(here, "card_db_example.json")
    return load_card_db(path)

_DB_CACHE = None
def _db():
    global _DB_CACHE
    if _DB_CACHE is None:
        _DB_CACHE = _CARD_DB()
    return _DB_CACHE

def _card(name: str):
    return _db()[name]

def _card_type(name: str) -> str:
    return _card(name)["type"]

def _card_weakness(name: str) -> str:
    return _card(name)["weakness"]
