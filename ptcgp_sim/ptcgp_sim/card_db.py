
from __future__ import annotations
import json, os, re
from typing import Dict, List, Tuple, TypedDict

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
    set: str
    card_id: str

# ---------- Variant-aware DB loading ----------

def default_card_db_path() -> str:
    here = os.path.dirname(__file__)
    for fname in ["all_cards_versioned.json", "all_cards.json", "card_db_eevee_grove.json", "card_db_example.json"]:
        p = os.path.join(here, fname)
        if os.path.exists(p):
            return p
    raise FileNotFoundError("No card DB found.")

def load_card_db_list(path: str) -> Dict[str, Card]:
    arr = json.load(open(path, "r"))
    db: Dict[str, Card] = {}
    for c in arr:
        key = c.get("card_id") or c["name"]
        db[key] = c
    return db

def build_indexes(db: Dict[str, Card]) -> Tuple[Dict[str, List[str]], Dict[str, Card]]:
    name_to_ids: Dict[str, List[str]] = {}
    id_to_card: Dict[str, Card] = {}
    for cid, card in db.items():
        id_to_card[cid] = card
        base = card["name"]
        name_to_ids.setdefault(base, []).append(cid)
    return name_to_ids, id_to_card

_ALIAS_PATTERNS = [
    (re.compile(r"^(.*)\s*\(([^)]+)\)\s*$"), lambda m: f"{m.group(1).strip()} [{m.group(2).strip()}]"),
    (re.compile(r"^(.*)\s*\[([^\]]+)\]\s*$"), lambda m: f"{m.group(1).strip()} [{m.group(2).strip()}]"),
]

def normalize_card_key(k: str) -> str:
    s = k.strip()
    for pat, repl in _ALIAS_PATTERNS:
        m = pat.match(s)
        if m:
            return repl(m)
    return s
