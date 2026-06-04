from powerguess.reading import Reading


def test_measured_sources():
    assert Reading(5, 5, 1, "ina219").measured is True
    assert Reading(5, 5, 1, "powerstat").measured is True
    assert Reading(5, 5, 1, "battery").measured is True
    assert Reading(5, 5, 1, "estimate", error_margin=2).measured is False


def test_as_dict():
    d = Reading(5.123, 5.0, 1.024, "estimate", error_margin=1.5).as_dict()
    assert d == {"power": 5.123, "voltage": 5.0, "current": 1.024,
                 "source": "estimate", "measured": False, "error_margin": 1.5}


def test_immutable():
    import dataclasses
    import pytest
    r = Reading(5, 5, 1, "ina219")
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.power = 9
