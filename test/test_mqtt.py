import json

import pytest

from powerguess.config import Config
from powerguess.mqtt_client import MQTTClient
from powerguess.reading import Reading


class FakeClient:
    def __init__(self):
        self.published = []
        self.on_connect = self.on_disconnect = None

    def username_pw_set(self, *a):
        pass

    def connect(self, *a, **k):
        pass

    def loop_start(self):
        pass

    def loop_stop(self):
        pass

    def disconnect(self):
        pass

    def publish(self, topic, payload, qos=0, retain=False):
        self.published.append((topic, json.loads(payload)))


@pytest.fixture
def client_with_battery():
    fake = FakeClient()
    c = MQTTClient(has_battery=True, client=fake)
    c._connected = True
    return c, fake


def test_discovery_without_battery():
    fake = FakeClient()
    c = MQTTClient(has_battery=False, client=fake)
    c._connected = True
    c.publish_discovery()
    keys = [t.split("/")[-2] for t, _ in fake.published]
    assert keys == ["power", "current", "voltage", "energy", "source",
                    "error_margin", "model"]
    energy = [p for t, p in fake.published if t.endswith("/energy/config")][0]
    assert energy["device_class"] == "energy"
    assert energy["state_class"] == "total_increasing"


def test_discovery_with_battery(client_with_battery):
    c, fake = client_with_battery
    c.publish_discovery()
    topics = [t for t, _ in fake.published]
    assert any("battery_level" in t for t in topics)
    assert any("binary_sensor" in t and "charging" in t for t in topics)
    assert len(topics) == 11  # 7 core + 4 battery


def test_publish_reading_carries_provenance_and_energy(client_with_battery):
    c, fake = client_with_battery
    r = Reading(5.1, 5.0, 1.02, "estimate", error_margin=1.5)
    assert c.publish_reading(r, energy_wh=1234.5, force=True) is True
    topic, payload = fake.published[-1]
    assert topic == "powerguess/state"
    assert payload["source"] == "estimate" and payload["measured"] is False
    assert payload["error_margin"] == 1.5
    assert payload["energy"] == round(1234.5 / 1000, 4)


def test_delta_publishing(client_with_battery):
    c, fake = client_with_battery
    Config.PUBLISH_DELTA = 0.5
    assert c.publish_reading(Reading(5.0, 5, 1, "estimate"), force=True) is True
    # within PUBLISH_INTERVAL and below delta -> suppressed
    assert c.publish_reading(Reading(5.2, 5, 1, "estimate")) is False
    # jump beyond delta -> published immediately
    assert c.publish_reading(Reading(9.0, 5, 1.8, "estimate")) is True


def test_publish_battery(client_with_battery):
    c, fake = client_with_battery
    c.publish_battery({"capacity": 79, "status": "Charging", "power": 9.1,
                       "voltage": 16.9})
    topic, payload = fake.published[-1]
    assert topic == "powerguess/battery"
    assert payload["charging"] is True and payload["level"] == 79
