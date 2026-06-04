"""powerguess MQTT bridge configuration — all settings via environment variables."""

import os


class Config:
    """Static config holder populated once at startup."""

    # Monitor
    MEASURE_INTERVAL: float = float(os.getenv("MEASURE_INTERVAL", "5"))
    SMOOTH: bool = os.getenv("SMOOTH", "false").lower() == "true"
    PREFER_BATTERY: bool = os.getenv("PREFER_BATTERY", "false").lower() == "true"
    PUBLISH_INTERVAL: float = float(os.getenv("PUBLISH_INTERVAL", "5"))

    # MQTT
    MQTT_HOST: str = os.getenv("MQTT_HOST", "localhost")
    MQTT_PORT: int = int(os.getenv("MQTT_PORT", "1883"))
    MQTT_USER = os.getenv("MQTT_USER") or None
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD") or None
    MQTT_TOPIC_PREFIX: str = os.getenv("MQTT_TOPIC_PREFIX", "powerguess")
    MQTT_CLIENT_ID: str = os.getenv("MQTT_CLIENT_ID", "powerguess-client")
    MQTT_QOS: int = int(os.getenv("MQTT_QOS", "0"))
    MQTT_RETAIN: bool = os.getenv("MQTT_RETAIN", "true").lower() == "true"
    MQTT_KEEPALIVE: int = int(os.getenv("MQTT_KEEPALIVE", "60"))
    MQTT_RETRY_COUNT: int = int(os.getenv("MQTT_RETRY_COUNT", "5"))
    MQTT_RETRY_MAX_BACKOFF: int = int(os.getenv("MQTT_RETRY_MAX_BACKOFF", "30"))
    MQTT_CONNECT_TIMEOUT: float = float(os.getenv("MQTT_CONNECT_TIMEOUT", "2.0"))

    # Home Assistant
    HA_ENABLED: bool = os.getenv("HA_ENABLED", "true").lower() == "true"
    HA_DISCOVERY_PREFIX: str = os.getenv("HA_DISCOVERY_PREFIX", "homeassistant")
    DEVICE_NAME: str = os.getenv("DEVICE_NAME", "PowerGuess")
    DEVICE_ID: str = os.getenv("DEVICE_ID", "powerguess_01")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
