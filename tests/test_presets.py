import pytest
from calcflow.presets.manager import load_preset, list_presets
from calcflow import PresetNotFoundError


def test_list_presets():
    presets = list_presets()
    assert "tight" in presets
    assert "sp-tight" in presets
    assert "freq" in presets
    assert "bader" in presets
    assert "single-point" in presets


def test_load_tight():
    params = load_preset("tight")
    assert params["IBRION"] == 2
    assert params["ISPIN"] == 1
    assert params["NSW"] == 500


def test_load_sp_tight():
    params = load_preset("sp-tight")
    assert params["ISPIN"] == 2


def test_load_freq():
    params = load_preset("freq")
    assert params["IBRION"] == 5
    assert params["NFREE"] == 2


def test_load_bader():
    params = load_preset("bader")
    assert params["LAECHG"] is True
    assert params["NSW"] == 0


def test_load_nonexistent():
    with pytest.raises(PresetNotFoundError):
        load_preset("nonexistent_preset_xyz")
