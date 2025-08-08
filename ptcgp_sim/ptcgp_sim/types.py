
from __future__ import annotations
from typing import Literal, Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

EnergyType = Literal["Fire","Water","Grass","Lightning","Psychic","Fighting","Darkness","Metal","Fairy","Colorless"]

class Phase(str, Enum):
    Start = "Start"
    Draw = "Draw"
    EnergyGen = "EnergyGen"
    Main = "Main"
    Attack = "Attack"
    Check = "Check"
    End = "End"

@dataclass
class EnergyZoneState:
    allowed_types: List[EnergyType]
    generated_this_turn: bool = False
    available_to_attach: List[EnergyType] = field(default_factory=list)

@dataclass
class PokemonInstance:
    card_id: str
    is_ex: bool
    hp: int
    max_hp: int
    attached_energy: List[EnergyType] = field(default_factory=list)
    status: str = "None"
    effects: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class PlayerState:
    deck: List[str]
    hand: List[str]
    discard: List[str]
    prize_points: int
    active: Optional[PokemonInstance]
    bench: List[PokemonInstance]
    energy_zone: EnergyZoneState
    effects: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class BattleState:
    turn: int
    current_player: int
    rng_seed: int
    preview_next_energy_type: Optional[EnergyType]
    players: Tuple[PlayerState, PlayerState]
    phase: Phase
    terminal: bool = False
    winner: Optional[int] = None
