
from .types import BattleState, Phase, EnergyType
from .rng import RNG

def energy_generation_phase(state: BattleState, rng: RNG, skip_first_turn: bool = True):
    p = state.players[state.current_player]

    if state.turn == 1 and state.current_player == 0 and skip_first_turn:
        # P1 T1: no energy generated this turn. Ensure preview exists.
        if state.preview_next_energy_type is None:
            state.preview_next_energy_type = rng.choice(p.energy_zone.allowed_types)
        return

    if state.preview_next_energy_type is None:
        state.preview_next_energy_type = rng.choice(p.energy_zone.allowed_types)

    this_turn_energy = state.preview_next_energy_type
    p.energy_zone.available_to_attach = [this_turn_energy]
    p.energy_zone.generated_this_turn = True

    # Sample next turn's preview now
    state.preview_next_energy_type = rng.choice(p.energy_zone.allowed_types)
