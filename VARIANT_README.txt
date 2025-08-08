
# Variant-aware Cards (PTCGP)

This package contains:
- `all_cards_versioned.json` — every card merged, with a `set` field and unique `card_id` like `Charmander [A1]`.
- `meta_decks_full_versioned.json` — sample meta decks normalized to those versioned IDs.

## How to install into your repo

1. Copy both files into your repo:
   ```
   ptcgp_sim/ptcgp_sim/all_cards_versioned.json
   ptcgp_sim/meta/meta_decks_full.json
   ```

2. Update your loader (in `ptcgp_sim/card_db.py`) to prefer the versioned DB and to accept `Name (SET)` or `Name [SET]`:
   ```python
   import re, json, os
   from typing import Dict

   def default_card_db_path() -> str:
       here = os.path.dirname(__file__)
       for fname in ["all_cards_versioned.json", "all_cards.json", "card_db_eevee_grove.json", "card_db_example.json"]:
           p = os.path.join(here, fname)
           if os.path.exists(p):
               return p
       raise FileNotFoundError("No card DB found.")

   def load_card_db_list(path: str) -> Dict[str, dict]:
       arr = json.load(open(path, "r"))
       return { (c.get("card_id") or c["name"]) : c for c in arr }

   def build_indexes(db: Dict[str, dict]):
       name_to_ids = {}
       id_to_card = {}
       for cid, card in db.items():
           id_to_card[cid] = card
           name_to_ids.setdefault(card["name"], []).append(cid)
       return name_to_ids, id_to_card

   def normalize_key(k: str) -> str:
       m = re.search(r"^(.*)\s*\[(.+)\]\s*$", k) or re.search(r"^(.*)\s*\((.+)\)\s*$", k)
       if m: return f"{m.group(1).strip()} [{m.group(2).strip()}]"
       return k.strip()
   ```

3. (Optional) Add a deck normalizer (`ptcgp_sim/deckio.py`) so your CLI can validate input decks and resolve ambiguous names. I can provide a ready file if you want to paste it.

4. Use the versioned meta file with your runner:
   ```bash
   ptcgp run-matches --deck-a my_deck.json --deck-b my_other_deck.json --games 500
   # or for the meta runner once we add it:
   ptcgp run-meta --meta ptcgp_sim/meta/meta_decks_full.json --games 1000
   ```

If you want me to **drop in the exact Python files** (`deckio.py`, CLI commands) so you can just copy/paste, say the word and I’ll generate them for you.
