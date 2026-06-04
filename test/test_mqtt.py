import json

import pytest

from powerguess.mqtt_client import MQTTClient


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


def test_discovery_with_battery(client_with_battery):
    c, fake = client_with_battery
    c.publish_discovery()
    topics = [t for t, _ in fake.published]
    assert "homeassistant/sensor/powerguess_01/power/config" in topics
    assert "homeassistant/sensor/powerguess_01/battery_level/config" in topics
    assert "homeassistant/binary_sensor/powerguess_01/charging/config" in topics
    assert len(topics) == 8  # power/current/voltage/model + 4 battery


def test_discovery_without_battery():
    fake = FakeClient()
    c = MQTTClient(has_battery=False, client=fake)
    c._connected = True
    c.publish_discovery()
    assert len(fake.published) == 4  # no battery group
    power_cfg = [p for t, p in fake.published if t.endswith("/power/config")][0]
    assert power_cfg["device_class"] == "power"
    assert power_cfg["unit_of_measurement"] == "W"
    assert power_cfg["state_topic"] == "powerguess/state"
    assert power_cfg["state_class"] == "measurement"


def test_publish_reading_payload(client_with_battery):
    c, fake = client_with_battery
    assert c.publish_reading(5.1, 5.0, 1.02, force=True) is True
    topic, payload = fake.published[-1]
    assert topic == "powerguess/state"
    assert payload["power"] == 5.1 and payload["voltage"] == 5.0
    assert "timestamp" in payload


def test_publish_reading_throttle(client_with_battery):
    c, fake = client_with_battery
    assert c.publish_reading(1, 1, 1, force=True) is True
    assert c.publish_reading(2, 2, 2) is False  # within PUBLISH_INTERVAL


def test_publish_battery(client_with_battery):
    c, fake = client_with_battery
    c.publish_battery({"capacity": 79, "status": "Charging", "power": 9.1,
                       "voltage": 16.9})
    topic, payload = fake.published[-1]
    assert topic == "powerguess/battery"
    assert payload["charging"] is True and payload["level"] == 79

    fake.published.clear()
    c.publish_battery(None)  # no battery -> no publish
    assert fake.published == []


def test_disconnected_drops_state():
    fake = FakeClient()
    c = MQTTClient(client=fake)  # not connected
    c.publish_reading(1, 1, 1, force=True)
    assert fake.published == []  # state dropped while disconnected
