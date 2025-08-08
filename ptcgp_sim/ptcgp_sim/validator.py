
from collections import Counter
from .types import EnergyType

def validate_deck(card_counts: dict[str,int], allowed_energy_types: list[EnergyType], deck_size: int = 20, max_copies_per_name: int = 2):
    total = sum(card_counts.values())
    assert total == deck_size, f"Deck must have {deck_size} cards, got {total}"
    for name, cnt in Counter(card_counts).items():
        assert cnt <= max_copies_per_name, f"Too many copies of {name}: {cnt}>{max_copies_per_name}"
    assert 1 <= len(allowed_energy_types) <= 3, "Must choose 1..3 energy types"
