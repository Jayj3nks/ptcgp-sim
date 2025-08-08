
from .types import BattleState, Phase
from .mechanics import _card
from .costs import cost_satisfied

def baseline_policy(sim, state: BattleState):
    actions = sim.legal_actions(state)
    p = state.players[state.current_player]

    # 1) Try to attack with any legal attack
    if p.active:
        card = _card(p.active.card_id)
        for atk in card.get("attacks", []):
            if cost_satisfied(p.active.attached_energy, atk.get("energy_cost", [])):
                return {"type":"Attack","attack_name":atk["name"]}

    # 2) Attach energy if we can
    for a in actions:
        if a.get("type") == "AttachEnergy":
            return a

    # 3) Otherwise pass
    return {"type":"Pass"}
