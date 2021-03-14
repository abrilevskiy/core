"""Constants for the Verisure integration."""
from datetime import timedelta
import logging

DOMAIN = "verisure"

LOGGER = logging.getLogger(__package__)

CONF_GIID = "giid"
CONF_LOCK_CODE_DIGITS = "lock_code_digits"
CONF_LOCK_DEFAULT_CODE = "lock_default_code"

DEFAULT_SCAN_INTERVAL = timedelta(minutes=1)
DEFAULT_LOCK_CODE_DIGITS = 4

SERVICE_CAPTURE_SMARTCAM = "capture_smartcam"
SERVICE_DISABLE_AUTOLOCK = "disable_autolock"
SERVICE_ENABLE_AUTOLOCK = "enable_autolock"

# Mapping of device types to a human readable name
DEVICE_TYPE_NAME = {
    "CAMERAPIR2": "Camera detector",
    "HOMEPAD1": "VoiceBox",
    "HUMIDITY1": "Climate sensor",
    "PIR2": "",
    "SIREN1": "Siren",
    "SMARTCAMERA1": "SmartCam",
    "SMOKE2": "Smoke detector",
    "SMOKE3": "Smoke detector",
    "VOICEBOX1": "VoiceBox",
    "WATER1": "Water detector",
}

# Legacy; to remove after YAML removal
CONF_CODE_DIGITS = "code_digits"
CONF_DEFAULT_LOCK_CODE = "default_lock_code"
