
from ptcgp_sim.costs import cost_satisfied

def test_cost_satisfied():
    assert cost_satisfied(["Water","Water","Colorless"], ["Water","Colorless"])
    assert not cost_satisfied(["Water"], ["Water","Colorless","Colorless"])
    assert cost_satisfied(["Water","Lightning"], ["Colorless","Colorless"])
