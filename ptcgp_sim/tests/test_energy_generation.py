
from ptcgp_sim.simulator import Simulator, MatchConfig
from ptcgp_sim.types import Phase
import os

def test_random_energy_typing_uniform():
    rules_path = os.path.join(os.path.dirname(__file__), "..", "ptcgp_sim", "rules.json")
    sim = Simulator(rules_path)
    cfg = MatchConfig(
        p0_deck={"Basic-A":10,"Basic-B":10},
        p0_energy_types=["Water","Lightning","Fire"],
        p1_deck={"Basic-A":10,"Basic-B":10},
        p1_energy_types=["Water"]
    )
    state = sim.reset(cfg)

    seen = set()
    # Run enough EnergyGen phases to see variability
    for _ in range(50):
        # advance to EnergyGen
        while state.phase != Phase.EnergyGen:
            state = sim.step(state, {"type":"Pass"})
        # generate energy
        state = sim.step(state, {"type":"Pass"})
        # after generation, p0 should have available_to_attach populated at least on their turns
        p = state.players[state.current_player]
        # Record previous player's available energy (after they generated)
        other = state.players[1 - state.current_player]
        seen.update(other.energy_zone.available_to_attach)
        # progress to next turn
        while state.phase != Phase.EnergyGen:
            state = sim.step(state, {"type":"Pass"})
        state = sim.step(state, {"type":"Pass"})
    assert len(seen) >= 2, f"Expected at least 2 distinct energy types seen; got {seen}"
