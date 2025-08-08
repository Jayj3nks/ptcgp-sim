
from __future__ import annotations
from typing import Dict, List, Optional, TypedDict

class Attack(TypedDict):
    name: str
    damage: int
    effect: str
    energy_cost: List[str]

class Card(TypedDict):
    name: str
    type: str
    hp: int
    abilities: List[dict]
    attacks: List[Attack]
    weakness: str
    retreat_cost: int
    card_type: str
    evolution_line: List[str]

def load_card_db(path: str) -> Dict[str, Card]:
    import json
    with open(path, 'r') as f:
        arr = json.load(f)
    db: Dict[str, Card] = {}
    for c in arr:
        db[c["name"]] = c  # assume unique names
    return db

def is_ex_card(card_name: str) -> bool:
    # Heuristic: names containing ' ex' are EX
    return " ex" in card_name


def default_card_db_path() -> str:
    import os
    here = os.path.dirname(__file__)
    merged = os.path.join(here, "all_cards.json")
    if os.path.exists(merged):
        return merged
    # fallback chain
    eg = os.path.join(here, "card_db_eevee_grove.json")
    if os.path.exists(eg):
        return eg
    return os.path.join(here, "card_db_example.json")
