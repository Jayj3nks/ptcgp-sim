
import typer, os, json
from rich import print as rprint
from .simulator import Simulator, MatchConfig
from .policy_baseline import baseline_policy
from .types import Phase

app = typer.Typer()

@app.command()
def demo(seed: int = 123):
    rules_path = os.path.join(os.path.dirname(__file__), "rules.json")
    card_db_path = os.path.join(os.path.dirname(__file__), "card_db_eevee_grove.json")
    sim = Simulator(rules_path, card_db_path)
    cfg = MatchConfig(
        p0_deck={"Eevee":10, "Pikachu?":10},  # placeholder names; replace with real
        p0_energy_types=["Water","Lightning"],
        p1_deck={"Eevee":10, "Farfetch'd":10},
        p1_energy_types=["Colorless"]
    )
    state = sim.reset(cfg)
    steps = 40
    for _ in range(steps):
        if state.phase == Phase.Main:
            act = baseline_policy(sim, state)
            state = sim.step(state, act)
        else:
            state = sim.step(state, {"type":"Pass"})
        if state.terminal:
            break
    rprint({"winner": state.winner, "p0_points": state.players[0].prize_points, "p1_points": state.players[1].prize_points})

@app.command()
def run_matches(deck_a: str, deck_b: str, games: int = 100, seed: int = 42, out: str = "results.json"):
    """Run A vs B for N games. Deck files are JSON: {"cards": {name: count}, "energy_types": [..]}"""
    rules_path = os.path.join(os.path.dirname(__file__), "rules.json")
    card_db_path = os.path.join(os.path.dirname(__file__), "card_db_eevee_grove.json")
    sim = Simulator(rules_path, card_db_path)

    da = json.load(open(deck_a))
    db = json.load(open(deck_b))

    wins_a = 0
    for i in range(games):
        cfg = MatchConfig(
            p0_deck=da["cards"],
            p0_energy_types=da["energy_types"],
            p1_deck=db["cards"],
            p1_energy_types=db["energy_types"],
            seed=seed + i
        )
        state = sim.reset(cfg)
        # play until terminal
        while not state.terminal:
            if state.phase == Phase.Main:
                act = baseline_policy(sim, state)
                state = sim.step(state, act)
            else:
                state = sim.step(state, {"type":"Pass"})
        if state.winner == 0:
            wins_a += 1
    results = {"games": games, "deck_a_wins": wins_a, "deck_b_wins": games-wins_a, "win_rate_a": wins_a/games}
    json.dump(results, open(out,"w"), indent=2)
    rprint(results)
