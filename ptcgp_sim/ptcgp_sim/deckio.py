
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

# Add near the top of deckio.py (or anywhere above validate_deck)
def is_ex(name: str) -> bool:
    n = name.strip().lower()
    return n.endswith(" ex") or " ex [" in n


# Replace your validate_deck in deckio.py with this version
def validate_deck(deck: Dict[str, int], energy_types: List[str]) -> Tuple[bool, List[str]]:
    """
    PTCGP rules (current):
      - 20 cards total
      - Max 2 copies per specific card
      - 'ex' counts as a different card line from the non-ex version
    """
    ok = True
    msgs: List[str] = []

    # total count
    total = sum(deck.values())
    if total != 20:
        ok = False
        msgs.append(f"Deck must have 20 cards, got {total}")

    # per-card limit = 2 (treat ex vs non-ex as separate)
    # NOTE: we already normalized to 'Name [SET]' IDs, but the copy limit
    # is per *name line*, not per set variant. So we collapse by (base_name, is_ex).
    _, name_to_ids, id_to_card = None, None, None
    try:
        db, name_to_ids, id_to_card = load_db()
    except Exception:
        # If DB load fails for some reason, fall back to per key
        for k, v in deck.items():
            if v > 2:
                ok = False
                msgs.append(f"Too many copies for {k}: {v} (>2)")
        return ok, msgs

    # map each entry to (base_name, ex_flag)
    def base_and_flag(card_id: str) -> Tuple[str, bool]:
        # Use DB if we have it; otherwise fall back to parsing the id itself.
        if id_to_card and card_id in id_to_card:
            name = id_to_card[card_id]["name"]
        else:
            # strip trailing [SET] if present
            name = re.sub(r"\s*\[[^\]]+\]$", "", card_id).strip()
        return (name if not is_ex(name) else name.replace(" ex", "").strip(), is_ex(name))

    grouped: Dict[Tuple[str, bool], int] = {}
    for cid, cnt in deck.items():
        base, exflag = base_and_flag(cid)
        grouped[(base, exflag)] = grouped.get((base, exflag), 0) + cnt

    for (base, exflag), cnt in grouped.items():
        if cnt > 2:
            label = f"{base}{' ex' if exflag else ''}"
            ok = False
            msgs.append(f"Too many copies of '{label}': {cnt} (>2)")

    # energy type sanity (keep simple; your deeper check happens in sim)
    if not (1 <= len(energy_types) <= 3):
        ok = False
        msgs.append("Energy types must be between 1 and 3.")

    return ok, msgs
