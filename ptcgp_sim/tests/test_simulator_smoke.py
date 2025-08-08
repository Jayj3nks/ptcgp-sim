
from ptcgp_sim.simulator import Simulator, MatchConfig
from ptcgp_sim.types import Phase
import os

def test_simulator_smoke():
    rules_path = os.path.join(os.path.dirname(__file__), "..", "ptcgp_sim", "rules.json")
    sim = Simulator(rules_path)
    cfg = MatchConfig(
        p0_deck={"Basic-A":10,"Basic-B":10},
        p0_energy_types=["Water","Lightning"],
        p1_deck={"Basic-A":10,"Basic-B":10},
        p1_energy_types=["Water"]
    )
    state = sim.reset(cfg)
    # step a few phases to ensure no crashes
    for _ in range(10):
        state = sim.step(state, {"type":"Pass"})
