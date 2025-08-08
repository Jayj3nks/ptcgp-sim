
import pytest
from ptcgp_sim.validator import validate_deck

def test_validate_deck_ok():
    validate_deck({"A":10,"B":10}, ["Water"])

def test_validate_deck_bad_size():
    with pytest.raises(AssertionError):
        validate_deck({"A":9,"B":10}, ["Water"])

def test_validate_deck_energy_types():
    with pytest.raises(AssertionError):
        validate_deck({"A":10,"B":10}, [])
    with pytest.raises(AssertionError):
        validate_deck({"A":10,"B":10}, ["W","X","Y","Z"])  # too many
