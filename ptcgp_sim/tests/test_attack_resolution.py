
from ptcgp_sim.simulator import Simulator, MatchConfig
from ptcgp_sim.types import Phase
import os, json

def test_attack_damage_applies():
    rules_path = os.path.join(os.path.dirname(__file__), "..", "ptcgp_sim", "rules.json")
    db_path = os.path.join(os.path.dirname(__file__), "..", "ptcgp_sim", "card_db_eevee_grove.json")
    sim = Simulator(rules_path, db_path)

    # Use two simple Colorless attackers from the DB if available; else fallback
    cfg = MatchConfig(
        p0_deck={"Farfetch'd":10, "Minccino":10},
        p0_energy_types=["Colorless"],
        p1_deck={"Minccino":10, "Cinccino":10},
        p1_energy_types=["Colorless"],
        seed=777
    )
    state = sim.reset(cfg)

    # Walk to EnergyGen for P0, generate and attach, then attack
    while state.phase != Phase.EnergyGen:
        state = sim.step(state, {"type":"Pass"})
    state = sim.step(state, {"type":"Pass"})  # generate
    # Main: attach
    state = sim.step(state, {"type":"AttachEnergy"})
    # Attack phase: attempt attack
    state = sim.step(state, {"type":"Attack","attack_name":"Leek Slap" if state.players[state.current_player].active.card_id == "Farfetch'd" else "Pound"})
    # Check
    state = sim.step(state, {"type":"Pass"})
    # End
    state = sim.step(state, {"type":"Pass"})
