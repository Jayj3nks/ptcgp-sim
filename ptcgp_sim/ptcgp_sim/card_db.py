# ptcgp_sim/ptcgp_sim/card_db.py
from __future__ import annotations

import json, os, re
from typing import Dict, List, Tuple, TypedDict, Any

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
    # variant-aware fields
    set: str
    card_id: str

# ---------------------------
# Preferred DB path (variant-aware first)
# ---------------------------

def default_card_db_path() -> str:
    here = os.path.dirname(__file__)
    for fname in [
        "all_cards_versioned.json",  # new merged DB (list of cards)
        "all_cards.json",            # legacy merged DB
        "card_db_eevee_grove.json",  # old single-set fallback
        "card_db_example.json",
    ]:
        p = os.path.join(here, fname)
        if os.path.exists(p):
            return p
    raise FileNotFoundError("No card DB found next to this module.")

# ---------------------------
# Loaders / indexes
# ---------------------------

def load_card_db_list(path: str) -> Dict[str, Card]:
    """
    Load a *list* of card dicts and key them by variant-aware id if present,
    otherwise by plain name.
    """
    arr = json.load(open(path, "r"))
    if isinstance(arr, dict):
        # Some very old DBs were dicts already
        return arr  # type: ignore[return-value]
    db: Dict[str, Card] = {}
    for c in arr:
        key = c.get("card_id") or c["name"]
        db[key] = c
    return db

def build_indexes(db: Dict[str, Card]) -> Tuple[Dict[str, List[str]], Dict[str, Card]]:
    """
    Build (base-name -> [card_ids]) and (card_id -> card).
    """
    name_to_ids: Dict[str, List[str]] = {}
    id_to_card: Dict[str, Card] = {}
    for cid, card in db.items():
        id_to_card[cid] = card
        base = card["name"]
        name_to_ids.setdefault(base, []).append(cid)
    return name_to_ids, id_to_card

# Accept "Name (SET)" or "Name [SET]" and normalize to "Name [SET]"
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

# ---------------------------
# Back-compat shims used by simulator.py
# ---------------------------

def load_card_db(path: str | None = None) -> Dict[str, Card]:
    """
    Old API expected by simulator.py. Loads whichever DB file exists and
    returns a mapping keyed by 'card_id' (if present) or 'name' otherwise.
    """
    if path is None:
        path = default_card_db_path()
    return load_card_db_list(path)

def is_ex_card(card_or_name: Any) -> bool:
    """
    Very simple heuristic used in some older logic: true if the card's name
    ends with 'ex'. Works for both dicts and strings.
    """
    if isinstance(card_or_name, dict):
        name = card_or_name.get("name", "")
    else:
        name = str(card_or_name)
    name = name.strip().lower()
    # handle things like "Charizard ex" or "Charizard ex [A2b]" (if someone passed an id)
    return name.endswith(" ex") or " ex [" in name
