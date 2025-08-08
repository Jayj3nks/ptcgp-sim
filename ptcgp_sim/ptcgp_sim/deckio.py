
from __future__ import annotations
import re, json
from typing import Dict, List, Tuple
from .card_db import default_card_db_path, load_card_db_list, build_indexes, normalize_card_key

def load_db():
    path = default_card_db_path()
    db = load_card_db_list(path)
    name_to_ids, id_to_card = build_indexes(db)
    return db, name_to_ids, id_to_card

def normalize_deck_dict(deck: Dict[str,int]) -> Tuple[Dict[str,int], List[str]]:
    db, name_to_ids, id_to_card = load_db()
    out: Dict[str,int] = {}
    warnings: List[str] = []
    for raw, cnt in deck.items():
        key = normalize_card_key(raw)
        if key in id_to_card:
            out[key] = out.get(key, 0) + cnt
            continue
        base = re.sub(r"\s*\[(.+)\]$", "", key).strip()
        if base in name_to_ids:
            ids = name_to_ids[base]
            if len(ids) == 1:
                out[ids[0]] = out.get(ids[0], 0) + cnt
            else:
                warnings.append(f"Ambiguous name '{raw}' -> candidates: {ids}")
        else:
            warnings.append(f"Unknown card name '{raw}'")
    return out, warnings

def validate_deck(deck: Dict[str,int], energy_types: List[str]) -> Tuple[bool, List[str]]:
    ok = True
    msgs: List[str] = []
    total = sum(deck.values())
    if total != 30:
        ok = False
        msgs.append(f"Deck must have 30 cards, got {total}")
    for k, v in deck.items():
        if v < 1:
            ok = False
            msgs.append(f"Non-positive count for {k}: {v}")
    if not (1 <= len(energy_types) <= 3):
        ok = False
        msgs.append("Energy types must be 1..3")
    return ok, msgs
