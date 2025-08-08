# ptcgp-sim

Minimal, deterministic simulator for **Pokémon TCG Pocket (PTCGP)** with the **Energy Zone random typing** mechanic (when >1 type is selected at deck build).

## Features
- 20-card decks, 3-point win condition, +20 weakness, no resistance.
- Energy Zone:
  - Generates **1 energy per turn** (except P1 turn 1).
  - If you selected **k types (1..3)** at deck build, each turn's type is sampled **uniformly at random** from those types.
  - **Preview** of next turn's energy is modeled by sampling one turn ahead.
  - **One attach per turn**, energy persists on Pokémon; **retreat discards** energy equal to cost.
- Deterministic RNG given a seed.
- Baseline policy + CLI for headless matches.
- Unit tests for random energy typing, deck validation, and smoke tests.

> This is a minimal framework intended for research and AI-agent integration. Extend with full card data, abilities, status effects, etc.

## Install & Run
```bash
# from repo root
pip install -e .

# run tests
pytest -q

# play a demo match with a fixed seed
ptcgp demo --seed 123
```

## Structure
- `ptcgp_sim/` — library code
- `tests/` — unit tests
- `ptcgp_sim/card_db_example.json` — tiny example DB (stub attacks, costs)

## GitHub
1. Create a new repo on GitHub (e.g., `ptcgp-sim`).
2. Locally:
```bash
git init
git add .
git commit -m "init: ptcgp-sim scaffold"
git branch -M main
git remote add origin git@github.com:Jayj3nks/ptcgp-sim.git
git push -u origin main
```
(Use HTTPS remote if you prefer.)

## License
MIT (adjust as you like).
