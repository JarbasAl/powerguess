import pytest

from powerguess.utils import transform_range


def test_transform_range_endpoints():
    assert transform_range(0, (0, 100), (2.7, 6.4)) == pytest.approx(2.7)
    assert transform_range(100, (0, 100), (2.7, 6.4)) == pytest.approx(6.4)


def test_transform_range_midpoint():
    assert transform_range(50, (0, 100), (2.7, 6.4)) == pytest.approx(4.55)


def test_transform_range_identity():
    assert transform_range(5, (0, 10), (0, 10)) == pytest.approx(5)


def test_get_model_env_override(monkeypatch):
    from powerguess.utils import get_model
    monkeypatch.setenv("POWERGUESS_MODEL", "Raspberry Pi 4 Model B")
    assert get_model() == "Raspberry Pi 4 Model B"
