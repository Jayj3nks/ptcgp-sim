
from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json, os
from .types import *
from .rng import RNG
from .energy import energy_generation_phase
from .validator import validate_deck
from .card_db import load_card_db, is_ex_card, default_card_db_path
from .mechanics import perform_attack, _card

@dataclass
class MatchConfig:
    p0_deck: Dict[str,int]
    p0_energy_types: List[EnergyType]
    p1_deck: Dict[str,int]
    p1_energy_types: List[EnergyType]
    seed: int = 123
    max_turns: int = 200

class Simulator:
    def __init__(self, rules_path: str, card_db_path: Optional[str] = None):
        with open(rules_path, 'r') as f:
            self.rules = json.load(f)
        if card_db_path is None:
            card_db_path = default_card_db_path()
        self.card_db = load_card_db(card_db_path)

    def reset(self, cfg: MatchConfig) -> BattleState:
        validate_deck(cfg.p0_deck, cfg.p0_energy_types)
        validate_deck(cfg.p1_deck, cfg.p1_energy_types)

        rng = RNG(cfg.seed)
        def draw_starting(deck_list, n):
            hand = []
            for _ in range(n):
                if deck_list:
                    hand.append(deck_list.pop(0))
            return hand

        def make_player(deck_counts, energy_types):
            # Expand to list and shuffle
            deck_list = []
            for cid, n in deck_counts.items():
                deck_list.extend([cid]*n)
            rng.random.shuffle(deck_list)

            # Active = first Pokémon we find; else take first card
            # (For minimal example: assume first card is Pokémon with hp)
            active_name = None
            for i, cid in enumerate(deck_list):
                if self.card_db.get(cid,{}).get("card_type") == "Pokémon":
                    active_name = deck_list.pop(i)
                    break
            if active_name is None:
                active_name = deck_list.pop(0)

            card = self.card_db.get(active_name, {"hp":100})
            active = PokemonInstance(card_id=active_name, is_ex=is_ex_card(active_name), hp=card.get("hp",100), max_hp=card.get("hp",100))

            bench = []
            hand = draw_starting(deck_list, self.rules["draw_rules"]["opening_hand"])

            return PlayerState(
                deck=deck_list,
                hand=hand,
                discard=[],
                prize_points=0,
                active=active,
                bench=bench,
                energy_zone=EnergyZoneState(allowed_types=energy_types)
            )

        p0 = make_player(cfg.p0_deck, cfg.p0_energy_types)
        p1 = make_player(cfg.p1_deck, cfg.p1_energy_types)

        state = BattleState(
            turn=1,
            current_player=0,
            rng_seed=cfg.seed,
            preview_next_energy_type=None,
            players=(p0,p1),
            phase=Phase.Start
        )
        self.cfg = cfg
        return state

    def legal_actions(self, state: BattleState):
        acts = []
        p = state.players[state.current_player]
        # Attach
        if p.energy_zone.available_to_attach:
            acts.append({"type":"AttachEnergy","target":"Active"})
        # Retreat (if enough attached energy to pay cost and bench exists)
        if p.active and p.active.attached_energy:
            retreat_cost = self.card_db.get(p.active.card_id,{}).get("retreat_cost",0)
            if len(p.active.attached_energy) >= retreat_cost and p.bench:
                acts.append({"type":"Retreat","benchIndex":0})
        # Attack(s) if any cost satisfied
        if p.active:
            card = self.card_db.get(p.active.card_id, {})
            for atk in card.get("attacks", []):
                acts.append({"type":"Attack","attack_name":atk["name"]})
        acts.append({"type":"Pass"})
        return acts

    def step(self, state: BattleState, action: dict) -> BattleState:
        p = state.players[state.current_player]
        opp = state.players[1 - state.current_player]

        if state.phase == Phase.Start:
            state.phase = Phase.Draw
            return state

        if state.phase == Phase.Draw:
            # draw 1 unless deck empty
            if p.deck and len(p.hand) < self.rules["draw_rules"]["hand_cap"]:
                p.hand.append(p.deck.pop(0))
            state.phase = Phase.EnergyGen
            return state

        if state.phase == Phase.EnergyGen:
            rng = RNG(state.rng_seed + state.turn*17 + state.current_player*101)
            energy_generation_phase(state, rng, skip_first_turn=self.rules["going_first_rules"]["skip_energy_generation_on_turn1"])
            state.phase = Phase.Main
            return state

        if state.phase == Phase.Main:
            t = action.get("type")
            if t == "AttachEnergy" and p.energy_zone.available_to_attach:
                energy = p.energy_zone.available_to_attach.pop()
                if p.active:
                    p.active.attached_energy.append(energy)
                state.phase = Phase.Attack
                return state
            elif t == "Retreat" and p.bench and p.active:
                cost = self.card_db.get(p.active.card_id,{}).get("retreat_cost",0)
                if len(p.active.attached_energy) >= cost:
                    # discard any cost energies
                    p.active.attached_energy = p.active.attached_energy[cost:]
                    # swap with bench index 0 for simplicity
                    p.active, p.bench[0] = p.bench[0], p.active
                state.phase = Phase.Attack
                return state
            else:
                # proceed to Attack phase
                state.phase = Phase.Attack
                return state

        if state.phase == Phase.Attack:
            if action.get("type") == "Attack" and p.active:
                # find attack in DB
                card = self.card_db.get(p.active.card_id, {})
                atk_name = action.get("attack_name")
                for atk in card.get("attacks", []):
                    if atk["name"] == atk_name:
                        perform_attack(state, atk)
                        break
            state.phase = Phase.Check
            return state

        if state.phase == Phase.Check:
            # Loss if field empty
            for i, pl in enumerate(state.players):
                if pl.active is None and not pl.bench:
                    state.terminal = True
                    state.winner = 1 - i
                    return state
            # Points to win
            for i, pl in enumerate(state.players):
                if pl.prize_points >= self.rules["win"]["points_to_win"]:
                    state.terminal = True
                    state.winner = i
                    return state
            # advance
            state.phase = Phase.End
            return state

        if state.phase == Phase.End:
            # turn rotate or end by max turns
            state.current_player = 1 - state.current_player
            if state.current_player == 0:
                state.turn += 1
            if state.turn > self.cfg.max_turns:
                state.terminal = True
                state.winner = None
            state.phase = Phase.Start
            return state

        return state
