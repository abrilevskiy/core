"""Support for Xiaomi Mi Air Purifier and Xiaomi Mi Air Humidifier."""
import asyncio
from enum import Enum
from functools import partial
import logging

from miio import (
    AirFresh,
    AirHumidifier,
    AirHumidifierMiot,
    AirPurifier,
    AirPurifierMB4,
    AirPurifierMiot,
    DeviceException,
)
from miio.airfresh import (
    LedBrightness as AirfreshLedBrightness,
    OperationMode as AirfreshOperationMode,
)
from miio.airhumidifier import (
    LedBrightness as AirhumidifierLedBrightness,
    OperationMode as AirhumidifierOperationMode,
)
from miio.airhumidifier_miot import (
    LedBrightness as AirhumidifierMiotLedBrightness,
    OperationMode as AirhumidifierMiotOperationMode,
    PressedButton as AirhumidifierPressedButton,
)
from miio.airpurifier import (
    LedBrightness as AirpurifierLedBrightness,
    OperationMode as AirpurifierOperationMode,
)
from miio.airpurifier_miot import (
    LedBrightness as AirpurifierMiotLedBrightness,
    OperationMode as AirpurifierMiotOperationMode,
)
import voluptuous as vol

from homeassistant.components.fan import (
    PLATFORM_SCHEMA,
    SPEED_HIGH,
    SPEED_LOW,
    SPEED_MEDIUM,
    SUPPORT_SET_SPEED,
    FanEntity,
)
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_MODE,
    ATTR_TEMPERATURE,
    CONF_HOST,
    CONF_NAME,
    CONF_TOKEN,
)
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_DEVICE,
    CONF_FLOW_TYPE,
    DOMAIN,
    MODEL_AIRHUMIDIFIER_CA1,
    MODEL_AIRHUMIDIFIER_CA4,
    MODEL_AIRHUMIDIFIER_CB1,
    MODEL_AIRPURIFIER_2S,
    MODEL_AIRPURIFIER_3,
    MODEL_AIRPURIFIER_3C,
    MODEL_AIRPURIFIER_3H,
    MODEL_AIRPURIFIER_PRO,
    MODEL_AIRPURIFIER_PRO_V7,
    MODEL_AIRPURIFIER_V3,
    MODELS_FAN,
    MODELS_HUMIDIFIER_MIOT,
    MODELS_PURIFIER_MIOT,
    SERVICE_RESET_FILTER,
    SERVICE_SET_AUTO_DETECT_OFF,
    SERVICE_SET_AUTO_DETECT_ON,
    SERVICE_SET_BUZZER_OFF,
    SERVICE_SET_BUZZER_ON,
    SERVICE_SET_CHILD_LOCK_OFF,
    SERVICE_SET_CHILD_LOCK_ON,
    SERVICE_SET_DRY_OFF,
    SERVICE_SET_DRY_ON,
    SERVICE_SET_EXTRA_FEATURES,
    SERVICE_SET_FAN_LED_OFF,
    SERVICE_SET_FAN_LED_ON,
    SERVICE_SET_FAN_LEVEL,
    SERVICE_SET_FAVORITE_LEVEL,
    SERVICE_SET_LEARN_MODE_OFF,
    SERVICE_SET_LEARN_MODE_ON,
    SERVICE_SET_LED_BRIGHTNESS,
    SERVICE_SET_MOTOR_SPEED,
    SERVICE_SET_TARGET_HUMIDITY,
    SERVICE_SET_VOLUME,
)
from .device import XiaomiMiioEntity

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Xiaomi Miio Device"
DATA_KEY = "fan.xiaomi_miio"

CONF_MODEL = "model"


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): vol.All(cv.string, vol.Length(min=32, max=32)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_MODEL): vol.In(MODELS_FAN),
    }
)

ATTR_MODEL = "model"

# Air Purifier
ATTR_HUMIDITY = "humidity"
ATTR_AIR_QUALITY_INDEX = "aqi"
ATTR_FILTER_HOURS_USED = "filter_hours_used"
ATTR_FILTER_LIFE = "filter_life_remaining"
ATTR_FAVORITE_LEVEL = "favorite_level"
ATTR_BUZZER = "buzzer"
ATTR_CHILD_LOCK = "child_lock"
ATTR_LED = "led"
ATTR_LED_BRIGHTNESS = "led_brightness"
ATTR_MOTOR_SPEED = "motor_speed"
ATTR_AVERAGE_AIR_QUALITY_INDEX = "average_aqi"
ATTR_PURIFY_VOLUME = "purify_volume"
ATTR_BRIGHTNESS = "brightness"
ATTR_LEVEL = "level"
ATTR_FAN_LEVEL = "fan_level"
ATTR_MOTOR2_SPEED = "motor2_speed"
ATTR_ILLUMINANCE = "illuminance"
ATTR_FILTER_RFID_PRODUCT_ID = "filter_rfid_product_id"
ATTR_FILTER_RFID_TAG = "filter_rfid_tag"
ATTR_FILTER_TYPE = "filter_type"
ATTR_LEARN_MODE = "learn_mode"
ATTR_SLEEP_TIME = "sleep_time"
ATTR_SLEEP_LEARN_COUNT = "sleep_mode_learn_count"
ATTR_EXTRA_FEATURES = "extra_features"
ATTR_FEATURES = "features"
ATTR_TURBO_MODE_SUPPORTED = "turbo_mode_supported"
ATTR_AUTO_DETECT = "auto_detect"
ATTR_SLEEP_MODE = "sleep_mode"
ATTR_VOLUME = "volume"
ATTR_USE_TIME = "use_time"
ATTR_BUTTON_PRESSED = "button_pressed"

# Air Humidifier
ATTR_TARGET_HUMIDITY = "target_humidity"
ATTR_TRANS_LEVEL = "trans_level"
ATTR_HARDWARE_VERSION = "hardware_version"

# Air Humidifier CA
# ATTR_MOTOR_SPEED = "motor_speed"
ATTR_DEPTH = "depth"
ATTR_DRY = "dry"

# Air Humidifier CA4
ATTR_ACTUAL_MOTOR_SPEED = "actual_speed"
ATTR_FAHRENHEIT = "fahrenheit"
ATTR_FAULT = "fault"

# Air Fresh
ATTR_CO2 = "co2"

# Map attributes to properties of the state object
AVAILABLE_ATTRIBUTES_AIRPURIFIER_COMMON = {
    ATTR_TEMPERATURE: "temperature",
    ATTR_HUMIDITY: "humidity",
    ATTR_AIR_QUALITY_INDEX: "aqi",
    ATTR_MODE: "mode",
    ATTR_FILTER_HOURS_USED: "filter_hours_used",
    ATTR_FILTER_LIFE: "filter_life_remaining",
    ATTR_FAVORITE_LEVEL: "favorite_level",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_LED: "led",
    ATTR_MOTOR_SPEED: "motor_speed",
    ATTR_AVERAGE_AIR_QUALITY_INDEX: "average_aqi",
    ATTR_LEARN_MODE: "learn_mode",
    ATTR_EXTRA_FEATURES: "extra_features",
    ATTR_TURBO_MODE_SUPPORTED: "turbo_mode_supported",
    ATTR_BUTTON_PRESSED: "button_pressed",
}

AVAILABLE_ATTRIBUTES_AIRPURIFIER = {
    **AVAILABLE_ATTRIBUTES_AIRPURIFIER_COMMON,
    ATTR_PURIFY_VOLUME: "purify_volume",
    ATTR_SLEEP_TIME: "sleep_time",
    ATTR_SLEEP_LEARN_COUNT: "sleep_mode_learn_count",
    ATTR_AUTO_DETECT: "auto_detect",
    ATTR_USE_TIME: "use_time",
    ATTR_BUZZER: "buzzer",
    ATTR_LED_BRIGHTNESS: "led_brightness",
    ATTR_SLEEP_MODE: "sleep_mode",
}

AVAILABLE_ATTRIBUTES_AIRPURIFIER_PRO = {
    **AVAILABLE_ATTRIBUTES_AIRPURIFIER_COMMON,
    ATTR_PURIFY_VOLUME: "purify_volume",
    ATTR_USE_TIME: "use_time",
    ATTR_FILTER_RFID_PRODUCT_ID: "filter_rfid_product_id",
    ATTR_FILTER_RFID_TAG: "filter_rfid_tag",
    ATTR_FILTER_TYPE: "filter_type",
    ATTR_ILLUMINANCE: "illuminance",
    ATTR_MOTOR2_SPEED: "motor2_speed",
    ATTR_VOLUME: "volume",
    # perhaps supported but unconfirmed
    ATTR_AUTO_DETECT: "auto_detect",
    ATTR_SLEEP_TIME: "sleep_time",
    ATTR_SLEEP_LEARN_COUNT: "sleep_mode_learn_count",
}

AVAILABLE_ATTRIBUTES_AIRPURIFIER_PRO_V7 = {
    **AVAILABLE_ATTRIBUTES_AIRPURIFIER_COMMON,
    ATTR_FILTER_RFID_PRODUCT_ID: "filter_rfid_product_id",
    ATTR_FILTER_RFID_TAG: "filter_rfid_tag",
    ATTR_FILTER_TYPE: "filter_type",
    ATTR_ILLUMINANCE: "illuminance",
    ATTR_MOTOR2_SPEED: "motor2_speed",
    ATTR_VOLUME: "volume",
}

AVAILABLE_ATTRIBUTES_AIRPURIFIER_2S = {
    **AVAILABLE_ATTRIBUTES_AIRPURIFIER_COMMON,
    ATTR_BUZZER: "buzzer",
    ATTR_FILTER_RFID_PRODUCT_ID: "filter_rfid_product_id",
    ATTR_FILTER_RFID_TAG: "filter_rfid_tag",
    ATTR_FILTER_TYPE: "filter_type",
    ATTR_ILLUMINANCE: "illuminance",
}

AVAILABLE_ATTRIBUTES_AIRPURIFIER_3 = {
    ATTR_TEMPERATURE: "temperature",
    ATTR_HUMIDITY: "humidity",
    ATTR_AIR_QUALITY_INDEX: "aqi",
    ATTR_MODE: "mode",
    ATTR_FILTER_HOURS_USED: "filter_hours_used",
    ATTR_FILTER_LIFE: "filter_life_remaining",
    ATTR_FAVORITE_LEVEL: "favorite_level",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_LED: "led",
    ATTR_MOTOR_SPEED: "motor_speed",
    ATTR_AVERAGE_AIR_QUALITY_INDEX: "average_aqi",
    ATTR_PURIFY_VOLUME: "purify_volume",
    ATTR_USE_TIME: "use_time",
    ATTR_BUZZER: "buzzer",
    ATTR_LED_BRIGHTNESS: "led_brightness",
    ATTR_FILTER_RFID_PRODUCT_ID: "filter_rfid_product_id",
    ATTR_FILTER_RFID_TAG: "filter_rfid_tag",
    ATTR_FILTER_TYPE: "filter_type",
    ATTR_FAN_LEVEL: "fan_level",
}

AVAILABLE_ATTRIBUTES_AIRPURIFIER_3C = {
    ATTR_AIR_QUALITY_INDEX: "aqi",
    ATTR_MODE: "mode",
    ATTR_FILTER_HOURS_USED: "filter_hours_used",
    ATTR_FILTER_LIFE: "filter_life_remaining",
    ATTR_FAVORITE_LEVEL: "favorite_rpm",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_MOTOR_SPEED: "motor_speed",
    ATTR_BUZZER: "buzzer",
    ATTR_LED_BRIGHTNESS: "led_brightness_level",
}

AVAILABLE_ATTRIBUTES_AIRPURIFIER_V3 = {
    # Common set isn't used here. It's a very basic version of the device.
    ATTR_AIR_QUALITY_INDEX: "aqi",
    ATTR_MODE: "mode",
    ATTR_LED: "led",
    ATTR_BUZZER: "buzzer",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_ILLUMINANCE: "illuminance",
    ATTR_FILTER_HOURS_USED: "filter_hours_used",
    ATTR_FILTER_LIFE: "filter_life_remaining",
    ATTR_MOTOR_SPEED: "motor_speed",
    # perhaps supported but unconfirmed
    ATTR_AVERAGE_AIR_QUALITY_INDEX: "average_aqi",
    ATTR_VOLUME: "volume",
    ATTR_MOTOR2_SPEED: "motor2_speed",
    ATTR_FILTER_RFID_PRODUCT_ID: "filter_rfid_product_id",
    ATTR_FILTER_RFID_TAG: "filter_rfid_tag",
    ATTR_FILTER_TYPE: "filter_type",
    ATTR_PURIFY_VOLUME: "purify_volume",
    ATTR_LEARN_MODE: "learn_mode",
    ATTR_SLEEP_TIME: "sleep_time",
    ATTR_SLEEP_LEARN_COUNT: "sleep_mode_learn_count",
    ATTR_EXTRA_FEATURES: "extra_features",
    ATTR_AUTO_DETECT: "auto_detect",
    ATTR_USE_TIME: "use_time",
    ATTR_BUTTON_PRESSED: "button_pressed",
}

AVAILABLE_ATTRIBUTES_AIRHUMIDIFIER_COMMON = {
    ATTR_TEMPERATURE: "temperature",
    ATTR_HUMIDITY: "humidity",
    ATTR_MODE: "mode",
    ATTR_BUZZER: "buzzer",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_TARGET_HUMIDITY: "target_humidity",
    ATTR_LED_BRIGHTNESS: "led_brightness",
    ATTR_USE_TIME: "use_time",
}

AVAILABLE_ATTRIBUTES_AIRHUMIDIFIER = {
    **AVAILABLE_ATTRIBUTES_AIRHUMIDIFIER_COMMON,
    ATTR_TRANS_LEVEL: "trans_level",
    ATTR_BUTTON_PRESSED: "button_pressed",
    ATTR_HARDWARE_VERSION: "hardware_version",
}

AVAILABLE_ATTRIBUTES_AIRHUMIDIFIER_CA_AND_CB = {
    **AVAILABLE_ATTRIBUTES_AIRHUMIDIFIER_COMMON,
    ATTR_MOTOR_SPEED: "motor_speed",
    ATTR_DEPTH: "depth",
    ATTR_DRY: "dry",
    ATTR_HARDWARE_VERSION: "hardware_version",
}

AVAILABLE_ATTRIBUTES_AIRHUMIDIFIER_CA4 = {
    **AVAILABLE_ATTRIBUTES_AIRHUMIDIFIER_COMMON,
    ATTR_ACTUAL_MOTOR_SPEED: "actual_speed",
    ATTR_BUTTON_PRESSED: "button_pressed",
    ATTR_DRY: "dry",
    ATTR_FAHRENHEIT: "fahrenheit",
    ATTR_MOTOR_SPEED: "motor_speed",
}

AVAILABLE_ATTRIBUTES_AIRFRESH = {
    ATTR_TEMPERATURE: "temperature",
    ATTR_AIR_QUALITY_INDEX: "aqi",
    ATTR_AVERAGE_AIR_QUALITY_INDEX: "average_aqi",
    ATTR_CO2: "co2",
    ATTR_HUMIDITY: "humidity",
    ATTR_MODE: "mode",
    ATTR_LED: "led",
    ATTR_LED_BRIGHTNESS: "led_brightness",
    ATTR_BUZZER: "buzzer",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_FILTER_LIFE: "filter_life_remaining",
    ATTR_FILTER_HOURS_USED: "filter_hours_used",
    ATTR_USE_TIME: "use_time",
    ATTR_MOTOR_SPEED: "motor_speed",
    ATTR_EXTRA_FEATURES: "extra_features",
}

OPERATION_MODES_AIRPURIFIER = ["Auto", "Silent", "Favorite", "Idle"]
OPERATION_MODES_AIRPURIFIER_PRO = ["Auto", "Silent", "Favorite"]
OPERATION_MODES_AIRPURIFIER_PRO_V7 = OPERATION_MODES_AIRPURIFIER_PRO
OPERATION_MODES_AIRPURIFIER_2S = ["Auto", "Silent", "Favorite"]
OPERATION_MODES_AIRPURIFIER_3 = ["Auto", "Silent", "Favorite", "Fan"]
OPERATION_MODES_AIRPURIFIER_V3 = [
    "Auto",
    "Silent",
    "Favorite",
    "Idle",
    "Medium",
    "High",
    "Strong",
]
OPERATION_MODES_AIRPURIFIER_3C = ["Auto", "Silent", "Favorite"]
OPERATION_MODES_AIRFRESH = ["Auto", "Silent", "Interval", "Low", "Middle", "Strong"]

SUCCESS = ["ok"]

FEATURE_SET_BUZZER = 1
FEATURE_SET_LED = 2
FEATURE_SET_CHILD_LOCK = 4
FEATURE_SET_LED_BRIGHTNESS = 8
FEATURE_SET_FAVORITE_LEVEL = 16
FEATURE_SET_AUTO_DETECT = 32
FEATURE_SET_LEARN_MODE = 64
FEATURE_SET_VOLUME = 128
FEATURE_RESET_FILTER = 256
FEATURE_SET_EXTRA_FEATURES = 512
FEATURE_SET_TARGET_HUMIDITY = 1024
FEATURE_SET_DRY = 2048
FEATURE_SET_FAN_LEVEL = 4096
FEATURE_SET_MOTOR_SPEED = 8192

FEATURE_FLAGS_AIRPURIFIER = (
    FEATURE_SET_BUZZER
    | FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_LED
    | FEATURE_SET_LED_BRIGHTNESS
    | FEATURE_SET_FAVORITE_LEVEL
    | FEATURE_SET_LEARN_MODE
    | FEATURE_RESET_FILTER
    | FEATURE_SET_EXTRA_FEATURES
)

FEATURE_FLAGS_AIRPURIFIER_PRO = (
    FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_LED
    | FEATURE_SET_FAVORITE_LEVEL
    | FEATURE_SET_AUTO_DETECT
    | FEATURE_SET_VOLUME
)

FEATURE_FLAGS_AIRPURIFIER_PRO_V7 = (
    FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_LED
    | FEATURE_SET_FAVORITE_LEVEL
    | FEATURE_SET_VOLUME
)

FEATURE_FLAGS_AIRPURIFIER_2S = (
    FEATURE_SET_BUZZER
    | FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_LED
    | FEATURE_SET_FAVORITE_LEVEL
)

FEATURE_FLAGS_AIRPURIFIER_3 = (
    FEATURE_SET_BUZZER
    | FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_LED
    | FEATURE_SET_FAVORITE_LEVEL
    | FEATURE_SET_FAN_LEVEL
    | FEATURE_SET_LED_BRIGHTNESS
)

FEATURE_FLAGS_AIRPURIFIER_3C = (
    FEATURE_SET_BUZZER
    | FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_LED
    | FEATURE_SET_FAVORITE_LEVEL
    | FEATURE_SET_FAN_LEVEL
    | FEATURE_SET_LED_BRIGHTNESS
)

FEATURE_FLAGS_AIRPURIFIER_V3 = (
    FEATURE_SET_BUZZER | FEATURE_SET_CHILD_LOCK | FEATURE_SET_LED
)

FEATURE_FLAGS_AIRHUMIDIFIER = (
    FEATURE_SET_BUZZER
    | FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_LED
    | FEATURE_SET_LED_BRIGHTNESS
    | FEATURE_SET_TARGET_HUMIDITY
)

FEATURE_FLAGS_AIRHUMIDIFIER_CA_AND_CB = FEATURE_FLAGS_AIRHUMIDIFIER | FEATURE_SET_DRY

FEATURE_FLAGS_AIRHUMIDIFIER_CA4 = (
    FEATURE_SET_BUZZER
    | FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_LED_BRIGHTNESS
    | FEATURE_SET_TARGET_HUMIDITY
    | FEATURE_SET_DRY
    | FEATURE_SET_MOTOR_SPEED
)

FEATURE_FLAGS_AIRFRESH = (
    FEATURE_SET_BUZZER
    | FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_LED
    | FEATURE_SET_LED_BRIGHTNESS
    | FEATURE_RESET_FILTER
    | FEATURE_SET_EXTRA_FEATURES
)

AIRPURIFIER_SERVICE_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTITY_ID): cv.entity_ids})

SERVICE_SCHEMA_LED_BRIGHTNESS = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_BRIGHTNESS): vol.All(vol.Coerce(int), vol.Clamp(min=0, max=2))}
)

SERVICE_SCHEMA_FAVORITE_LEVEL = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_LEVEL): vol.All(vol.Coerce(int), vol.Clamp(min=0, max=17))}
)

SERVICE_SCHEMA_FAN_LEVEL = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_LEVEL): vol.All(vol.Coerce(int), vol.Clamp(min=1, max=3))}
)

SERVICE_SCHEMA_VOLUME = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_VOLUME): vol.All(vol.Coerce(int), vol.Clamp(min=0, max=100))}
)

SERVICE_SCHEMA_EXTRA_FEATURES = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_FEATURES): cv.positive_int}
)

SERVICE_SCHEMA_TARGET_HUMIDITY = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {
        vol.Required(ATTR_HUMIDITY): vol.All(
            vol.Coerce(int), vol.In([30, 40, 50, 60, 70, 80])
        )
    }
)

SERVICE_SCHEMA_MOTOR_SPEED = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {
        vol.Required(ATTR_MOTOR_SPEED): vol.All(
            vol.Coerce(int), vol.Clamp(min=200, max=2000)
        )
    }
)

SERVICE_TO_METHOD = {
    SERVICE_SET_BUZZER_ON: {"method": "async_set_buzzer_on"},
    SERVICE_SET_BUZZER_OFF: {"method": "async_set_buzzer_off"},
    SERVICE_SET_FAN_LED_ON: {"method": "async_set_led_on"},
    SERVICE_SET_FAN_LED_OFF: {"method": "async_set_led_off"},
    SERVICE_SET_CHILD_LOCK_ON: {"method": "async_set_child_lock_on"},
    SERVICE_SET_CHILD_LOCK_OFF: {"method": "async_set_child_lock_off"},
    SERVICE_SET_AUTO_DETECT_ON: {"method": "async_set_auto_detect_on"},
    SERVICE_SET_AUTO_DETECT_OFF: {"method": "async_set_auto_detect_off"},
    SERVICE_SET_LEARN_MODE_ON: {"method": "async_set_learn_mode_on"},
    SERVICE_SET_LEARN_MODE_OFF: {"method": "async_set_learn_mode_off"},
    SERVICE_RESET_FILTER: {"method": "async_reset_filter"},
    SERVICE_SET_LED_BRIGHTNESS: {
        "method": "async_set_led_brightness",
        "schema": SERVICE_SCHEMA_LED_BRIGHTNESS,
    },
    SERVICE_SET_FAVORITE_LEVEL: {
        "method": "async_set_favorite_level",
        "schema": SERVICE_SCHEMA_FAVORITE_LEVEL,
    },
    SERVICE_SET_FAN_LEVEL: {
        "method": "async_set_fan_level",
        "schema": SERVICE_SCHEMA_FAN_LEVEL,
    },
    SERVICE_SET_VOLUME: {"method": "async_set_volume", "schema": SERVICE_SCHEMA_VOLUME},
    SERVICE_SET_EXTRA_FEATURES: {
        "method": "async_set_extra_features",
        "schema": SERVICE_SCHEMA_EXTRA_FEATURES,
    },
    SERVICE_SET_TARGET_HUMIDITY: {
        "method": "async_set_target_humidity",
        "schema": SERVICE_SCHEMA_TARGET_HUMIDITY,
    },
    SERVICE_SET_DRY_ON: {"method": "async_set_dry_on"},
    SERVICE_SET_DRY_OFF: {"method": "async_set_dry_off"},
    SERVICE_SET_MOTOR_SPEED: {
        "method": "async_set_motor_speed",
        "schema": SERVICE_SCHEMA_MOTOR_SPEED,
    },
}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Import Miio configuration from YAML."""
    _LOGGER.warning(
        "Loading Xiaomi Miio Fan via platform setup is deprecated. "
        "Please remove it from your configuration"
    )
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data=config,
        )
    )


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Fan from a config entry."""
    entities = []

    if config_entry.data[CONF_FLOW_TYPE] == CONF_DEVICE:
        if DATA_KEY not in hass.data:
            hass.data[DATA_KEY] = {}

        host = config_entry.data[CONF_HOST]
        token = config_entry.data[CONF_TOKEN]
        name = config_entry.title
        model = config_entry.data[CONF_MODEL]
        unique_id = config_entry.unique_id

        _LOGGER.debug("Initializing with host %s (token %s...)", host, token[:5])

        if model == MODEL_AIRPURIFIER_3C:
            air_purifier = AirPurifierMB4(host, token)
            entity = XiaomiAirPurifierMiot(name, air_purifier, config_entry, unique_id)
        elif model in MODELS_PURIFIER_MIOT:
            air_purifier = AirPurifierMiot(host, token)
            entity = XiaomiAirPurifierMiot(name, air_purifier, config_entry, unique_id)
        elif model.startswith("zhimi.airpurifier."):
            air_purifier = AirPurifier(host, token)
            entity = XiaomiAirPurifier(name, air_purifier, config_entry, unique_id)
        elif model in MODELS_HUMIDIFIER_MIOT:
            air_humidifier = AirHumidifierMiot(host, token)
            entity = XiaomiAirHumidifierMiot(
                name, air_humidifier, config_entry, unique_id
            )
        elif model.startswith("zhimi.humidifier."):
            air_humidifier = AirHumidifier(host, token, model=model)
            entity = XiaomiAirHumidifier(name, air_humidifier, config_entry, unique_id)
        elif model.startswith("zhimi.airfresh."):
            air_fresh = AirFresh(host, token)
            entity = XiaomiAirFresh(name, air_fresh, config_entry, unique_id)
        else:
            _LOGGER.error(
                "Unsupported device found! Please create an issue at "
                "https://github.com/syssi/xiaomi_airpurifier/issues "
                "and provide the following data: %s",
                model,
            )
            return

        hass.data[DATA_KEY][host] = entity
        entities.append(entity)

        async def async_service_handler(service):
            """Map services to methods on XiaomiAirPurifier."""
            method = SERVICE_TO_METHOD[service.service]
            params = {
                key: value
                for key, value in service.data.items()
                if key != ATTR_ENTITY_ID
            }
            entity_ids = service.data.get(ATTR_ENTITY_ID)
            if entity_ids:
                entities = [
                    entity
                    for entity in hass.data[DATA_KEY].values()
                    if entity.entity_id in entity_ids
                ]
            else:
                entities = hass.data[DATA_KEY].values()

            update_tasks = []

            for entity in entities:
                entity_method = getattr(entity, method["method"], None)
                if not entity_method:
                    continue
                await entity_method(**params)
                update_tasks.append(
                    hass.async_create_task(entity.async_update_ha_state(True))
                )

            if update_tasks:
                await asyncio.wait(update_tasks)

        for air_purifier_service in SERVICE_TO_METHOD:
            schema = SERVICE_TO_METHOD[air_purifier_service].get(
                "schema", AIRPURIFIER_SERVICE_SCHEMA
            )
            hass.services.async_register(
                DOMAIN, air_purifier_service, async_service_handler, schema=schema
            )

    async_add_entities(entities, update_before_add=True)


class XiaomiGenericDevice(XiaomiMiioEntity, FanEntity):
    """Representation of a generic Xiaomi device."""

    def __init__(self, name, device, entry, unique_id):
        """Initialize the generic Xiaomi device."""
        super().__init__(name, device, entry, unique_id)

        self._available = False
        self._state = None
        self._state_attrs = {ATTR_MODEL: self._model}
        self._device_features = FEATURE_SET_CHILD_LOCK
        self._skip_update = False

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_SET_SPEED

    @property
    def should_poll(self):
        """Poll the device."""
        return True

    @property
    def available(self):
        """Return true when state is known."""
        return self._available

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the device."""
        return self._state_attrs

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    @staticmethod
    def _extract_value_from_attribute(state, attribute):
        value = getattr(state, attribute)
        if isinstance(value, Enum):
            return value.value

        return value

    async def _try_command(self, mask_error, func, *args, **kwargs):
        """Call a miio device command handling error messages."""
        try:
            result = await self.hass.async_add_executor_job(
                partial(func, *args, **kwargs)
            )

            _LOGGER.debug("Response received from miio device: %s", result)

            return result == SUCCESS
        except DeviceException as exc:
            if self._available:
                _LOGGER.error(mask_error, exc)
                self._available = False

            return False

    #
    # The fan entity model has changed to use percentages and preset_modes
    # instead of speeds.
    #
    # Please review
    # https://developers.home-assistant.io/docs/core/entity/fan/
    #
    async def async_turn_on(
        self,
        speed: str = None,
        percentage: int = None,
        preset_mode: str = None,
        **kwargs,
    ) -> None:
        """Turn the device on."""
        if speed:
            # If operation mode was set the device must not be turned on.
            result = await self.async_set_speed(speed)
        else:
            result = await self._try_command(
                "Turning the miio device on failed.", self._device.on
            )

        if result:
            self._state = True
            self._skip_update = True

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the device off."""
        result = await self._try_command(
            "Turning the miio device off failed.", self._device.off
        )

        if result:
            self._state = False
            self._skip_update = True

    async def async_set_buzzer_on(self):
        """Turn the buzzer on."""
        if self._device_features & FEATURE_SET_BUZZER == 0:
            return

        await self._try_command(
            "Turning the buzzer of the miio device on failed.",
            self._device.set_buzzer,
            True,
        )

    async def async_set_buzzer_off(self):
        """Turn the buzzer off."""
        if self._device_features & FEATURE_SET_BUZZER == 0:
            return

        await self._try_command(
            "Turning the buzzer of the miio device off failed.",
            self._device.set_buzzer,
            False,
        )

    async def async_set_child_lock_on(self):
        """Turn the child lock on."""
        if self._device_features & FEATURE_SET_CHILD_LOCK == 0:
            return

        await self._try_command(
            "Turning the child lock of the miio device on failed.",
            self._device.set_child_lock,
            True,
        )

    async def async_set_child_lock_off(self):
        """Turn the child lock off."""
        if self._device_features & FEATURE_SET_CHILD_LOCK == 0:
            return

        await self._try_command(
            "Turning the child lock of the miio device off failed.",
            self._device.set_child_lock,
            False,
        )


class XiaomiAirPurifier(XiaomiGenericDevice):
    """Representation of a Xiaomi Air Purifier."""

    def __init__(self, name, device, entry, unique_id):
        """Initialize the plug switch."""
        super().__init__(name, device, entry, unique_id)

        if self._model == MODEL_AIRPURIFIER_PRO:
            self._device_features = FEATURE_FLAGS_AIRPURIFIER_PRO
            self._available_attributes = AVAILABLE_ATTRIBUTES_AIRPURIFIER_PRO
            self._speed_list = OPERATION_MODES_AIRPURIFIER_PRO
        elif self._model == MODEL_AIRPURIFIER_PRO_V7:
            self._device_features = FEATURE_FLAGS_AIRPURIFIER_PRO_V7
            self._available_attributes = AVAILABLE_ATTRIBUTES_AIRPURIFIER_PRO_V7
            self._speed_list = OPERATION_MODES_AIRPURIFIER_PRO_V7
        elif self._model == MODEL_AIRPURIFIER_2S:
            self._device_features = FEATURE_FLAGS_AIRPURIFIER_2S
            self._available_attributes = AVAILABLE_ATTRIBUTES_AIRPURIFIER_2S
            self._speed_list = OPERATION_MODES_AIRPURIFIER_2S
        elif self._model == MODEL_AIRPURIFIER_3 or self._model == MODEL_AIRPURIFIER_3H:
            self._device_features = FEATURE_FLAGS_AIRPURIFIER_3
            self._available_attributes = AVAILABLE_ATTRIBUTES_AIRPURIFIER_3
            self._speed_list = OPERATION_MODES_AIRPURIFIER_3
        elif self._model == MODEL_AIRPURIFIER_V3:
            self._device_features = FEATURE_FLAGS_AIRPURIFIER_V3
            self._available_attributes = AVAILABLE_ATTRIBUTES_AIRPURIFIER_V3
            self._speed_list = OPERATION_MODES_AIRPURIFIER_V3
        elif self._model == MODEL_AIRPURIFIER_3C:
            self._device_features = FEATURE_FLAGS_AIRPURIFIER_3C
            self._available_attributes = AVAILABLE_ATTRIBUTES_AIRPURIFIER_3C
            self._speed_list = OPERATION_MODES_AIRPURIFIER_3C
        else:
            self._device_features = FEATURE_FLAGS_AIRPURIFIER
            self._available_attributes = AVAILABLE_ATTRIBUTES_AIRPURIFIER
            self._speed_list = OPERATION_MODES_AIRPURIFIER

        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._state = state.is_on
            self._state_attrs.update(
                {
                    key: self._extract_value_from_attribute(state, value)
                    for key, value in self._available_attributes.items()
                }
            )

        except DeviceException as ex:
            if self._available:
                self._available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return self._speed_list

    @property
    def speed(self):
        """Return the current speed."""
        if self._state:
            return AirpurifierOperationMode(self._state_attrs[ATTR_MODE]).name

        return None

    async def async_set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        if self.supported_features & SUPPORT_SET_SPEED == 0:
            return

        _LOGGER.debug("Setting the operation mode to: %s", speed)

        await self._try_command(
            "Setting operation mode of the miio device failed.",
            self._device.set_mode,
            AirpurifierOperationMode[speed.title()],
        )

    async def async_set_led_on(self):
        """Turn the led on."""
        if self._device_features & FEATURE_SET_LED == 0:
            return

        await self._try_command(
            "Turning the led of the miio device off failed.", self._device.set_led, True
        )

    async def async_set_led_off(self):
        """Turn the led off."""
        if self._device_features & FEATURE_SET_LED == 0:
            return

        await self._try_command(
            "Turning the led of the miio device off failed.",
            self._device.set_led,
            False,
        )

    async def async_set_led_brightness(self, brightness: int = 2):
        """Set the led brightness."""
        if self._device_features & FEATURE_SET_LED_BRIGHTNESS == 0:
            return

        await self._try_command(
            "Setting the led brightness of the miio device failed.",
            self._device.set_led_brightness,
            AirpurifierLedBrightness(brightness),
        )

    async def async_set_favorite_level(self, level: int = 1):
        """Set the favorite level."""
        if self._device_features & FEATURE_SET_FAVORITE_LEVEL == 0:
            return

        await self._try_command(
            "Setting the favorite level of the miio device failed.",
            self._device.set_favorite_level,
            level,
        )

    async def async_set_fan_level(self, level: int = 1):
        """Set the favorite level."""
        if self._device_features & FEATURE_SET_FAN_LEVEL == 0:
            return

        await self._try_command(
            "Setting the fan level of the miio device failed.",
            self._device.set_fan_level,
            level,
        )

    async def async_set_auto_detect_on(self):
        """Turn the auto detect on."""
        if self._device_features & FEATURE_SET_AUTO_DETECT == 0:
            return

        await self._try_command(
            "Turning the auto detect of the miio device on failed.",
            self._device.set_auto_detect,
            True,
        )

    async def async_set_auto_detect_off(self):
        """Turn the auto detect off."""
        if self._device_features & FEATURE_SET_AUTO_DETECT == 0:
            return

        await self._try_command(
            "Turning the auto detect of the miio device off failed.",
            self._device.set_auto_detect,
            False,
        )

    async def async_set_learn_mode_on(self):
        """Turn the learn mode on."""
        if self._device_features & FEATURE_SET_LEARN_MODE == 0:
            return

        await self._try_command(
            "Turning the learn mode of the miio device on failed.",
            self._device.set_learn_mode,
            True,
        )

    async def async_set_learn_mode_off(self):
        """Turn the learn mode off."""
        if self._device_features & FEATURE_SET_LEARN_MODE == 0:
            return

        await self._try_command(
            "Turning the learn mode of the miio device off failed.",
            self._device.set_learn_mode,
            False,
        )

    async def async_set_volume(self, volume: int = 50):
        """Set the sound volume."""
        if self._device_features & FEATURE_SET_VOLUME == 0:
            return

        await self._try_command(
            "Setting the sound volume of the miio device failed.",
            self._device.set_volume,
            volume,
        )

    async def async_set_extra_features(self, features: int = 1):
        """Set the extra features."""
        if self._device_features & FEATURE_SET_EXTRA_FEATURES == 0:
            return

        await self._try_command(
            "Setting the extra features of the miio device failed.",
            self._device.set_extra_features,
            features,
        )

    async def async_reset_filter(self):
        """Reset the filter lifetime and usage."""
        if self._device_features & FEATURE_RESET_FILTER == 0:
            return

        await self._try_command(
            "Resetting the filter lifetime of the miio device failed.",
            self._device.reset_filter,
        )


class XiaomiAirPurifierMiot(XiaomiAirPurifier):
    """Representation of a Xiaomi Air Purifier (MiOT protocol)."""

    @property
    def speed(self):
        """Return the current speed."""
        if self._state:
            return AirpurifierMiotOperationMode(self._state_attrs[ATTR_MODE]).name

        return None

    async def async_set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        if self.supported_features & SUPPORT_SET_SPEED == 0:
            return

        _LOGGER.debug("Setting the operation mode to: %s", speed)

        await self._try_command(
            "Setting operation mode of the miio device failed.",
            self._device.set_mode,
            AirpurifierMiotOperationMode[speed.title()],
        )

    async def async_set_led_brightness(self, brightness: int = 2):
        """Set the led brightness."""
        if self._device_features & FEATURE_SET_LED_BRIGHTNESS == 0:
            return

        await self._try_command(
            "Setting the led brightness of the miio device failed.",
            self._device.set_led_brightness,
            AirpurifierMiotLedBrightness(brightness),
        )


class XiaomiAirHumidifier(XiaomiGenericDevice):
    """Representation of a Xiaomi Air Humidifier."""

    def __init__(self, name, device, entry, unique_id):
        """Initialize the plug switch."""
        super().__init__(name, device, entry, unique_id)

        if self._model in [MODEL_AIRHUMIDIFIER_CA1, MODEL_AIRHUMIDIFIER_CB1]:
            self._device_features = FEATURE_FLAGS_AIRHUMIDIFIER_CA_AND_CB
            self._available_attributes = AVAILABLE_ATTRIBUTES_AIRHUMIDIFIER_CA_AND_CB
            self._speed_list = [
                mode.name
                for mode in AirhumidifierOperationMode
                if mode is not AirhumidifierOperationMode.Strong
            ]
        elif self._model in [MODEL_AIRHUMIDIFIER_CA4]:
            self._device_features = FEATURE_FLAGS_AIRHUMIDIFIER_CA4
            self._available_attributes = AVAILABLE_ATTRIBUTES_AIRHUMIDIFIER_CA4
            self._speed_list = [SPEED_LOW, SPEED_MEDIUM, SPEED_HIGH]
        else:
            self._device_features = FEATURE_FLAGS_AIRHUMIDIFIER
            self._available_attributes = AVAILABLE_ATTRIBUTES_AIRHUMIDIFIER
            self._speed_list = [
                mode.name
                for mode in AirhumidifierOperationMode
                if mode is not AirhumidifierOperationMode.Auto
            ]

        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._state = state.is_on
            self._state_attrs.update(
                {
                    key: self._extract_value_from_attribute(state, value)
                    for key, value in self._available_attributes.items()
                }
            )

        except DeviceException as ex:
            if self._available:
                self._available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return self._speed_list

    @property
    def speed(self):
        """Return the current speed."""
        if self._state:
            return AirhumidifierOperationMode(self._state_attrs[ATTR_MODE]).name

        return None

    async def async_set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        if self.supported_features & SUPPORT_SET_SPEED == 0:
            return

        _LOGGER.debug("Setting the operation mode to: %s", speed)

        await self._try_command(
            "Setting operation mode of the miio device failed.",
            self._device.set_mode,
            AirhumidifierOperationMode[speed.title()],
        )

    async def async_set_led_brightness(self, brightness: int = 2):
        """Set the led brightness."""
        if self._device_features & FEATURE_SET_LED_BRIGHTNESS == 0:
            return

        await self._try_command(
            "Setting the led brightness of the miio device failed.",
            self._device.set_led_brightness,
            AirhumidifierLedBrightness(brightness),
        )

    async def async_set_target_humidity(self, humidity: int = 40):
        """Set the target humidity."""
        if self._device_features & FEATURE_SET_TARGET_HUMIDITY == 0:
            return

        await self._try_command(
            "Setting the target humidity of the miio device failed.",
            self._device.set_target_humidity,
            humidity,
        )

    async def async_set_dry_on(self):
        """Turn the dry mode on."""
        if self._device_features & FEATURE_SET_DRY == 0:
            return

        await self._try_command(
            "Turning the dry mode of the miio device off failed.",
            self._device.set_dry,
            True,
        )

    async def async_set_dry_off(self):
        """Turn the dry mode off."""
        if self._device_features & FEATURE_SET_DRY == 0:
            return

        await self._try_command(
            "Turning the dry mode of the miio device off failed.",
            self._device.set_dry,
            False,
        )


class XiaomiAirHumidifierMiot(XiaomiAirHumidifier):
    """Representation of a Xiaomi Air Humidifier (MiOT protocol)."""

    MODE_MAPPING = {
        AirhumidifierMiotOperationMode.Low: SPEED_LOW,
        AirhumidifierMiotOperationMode.Mid: SPEED_MEDIUM,
        AirhumidifierMiotOperationMode.High: SPEED_HIGH,
    }

    REVERSE_MODE_MAPPING = {v: k for k, v in MODE_MAPPING.items()}

    @property
    def speed(self):
        """Return the current speed."""
        if self._state:
            return self.MODE_MAPPING.get(
                AirhumidifierMiotOperationMode(self._state_attrs[ATTR_MODE])
            )

        return None

    @property
    def button_pressed(self):
        """Return the last button pressed."""
        if self._state:
            return AirhumidifierPressedButton(
                self._state_attrs[ATTR_BUTTON_PRESSED]
            ).name

        return None

    async def async_set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        await self._try_command(
            "Setting operation mode of the miio device failed.",
            self._device.set_mode,
            self.REVERSE_MODE_MAPPING[speed],
        )

    async def async_set_led_brightness(self, brightness: int = 2):
        """Set the led brightness."""
        if self._device_features & FEATURE_SET_LED_BRIGHTNESS == 0:
            return

        await self._try_command(
            "Setting the led brightness of the miio device failed.",
            self._device.set_led_brightness,
            AirhumidifierMiotLedBrightness(brightness),
        )

    async def async_set_motor_speed(self, motor_speed: int = 400):
        """Set the target motor speed."""
        if self._device_features & FEATURE_SET_MOTOR_SPEED == 0:
            return

        await self._try_command(
            "Setting the target motor speed of the miio device failed.",
            self._device.set_speed,
            motor_speed,
        )


class XiaomiAirFresh(XiaomiGenericDevice):
    """Representation of a Xiaomi Air Fresh."""

    def __init__(self, name, device, entry, unique_id):
        """Initialize the miio device."""
        super().__init__(name, device, entry, unique_id)

        self._device_features = FEATURE_FLAGS_AIRFRESH
        self._available_attributes = AVAILABLE_ATTRIBUTES_AIRFRESH
        self._speed_list = OPERATION_MODES_AIRFRESH
        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_executor_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._state = state.is_on
            self._state_attrs.update(
                {
                    key: self._extract_value_from_attribute(state, value)
                    for key, value in self._available_attributes.items()
                }
            )

        except DeviceException as ex:
            if self._available:
                self._available = False
                _LOGGER.error("Got exception while fetching the state: %s", ex)

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return self._speed_list

    @property
    def speed(self):
        """Return the current speed."""
        if self._state:
            return AirfreshOperationMode(self._state_attrs[ATTR_MODE]).name

        return None

    async def async_set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        if self.supported_features & SUPPORT_SET_SPEED == 0:
            return

        _LOGGER.debug("Setting the operation mode to: %s", speed)

        await self._try_command(
            "Setting operation mode of the miio device failed.",
            self._device.set_mode,
            AirfreshOperationMode[speed.title()],
        )

    async def async_set_led_on(self):
        """Turn the led on."""
        if self._device_features & FEATURE_SET_LED == 0:
            return

        await self._try_command(
            "Turning the led of the miio device off failed.", self._device.set_led, True
        )

    async def async_set_led_off(self):
        """Turn the led off."""
        if self._device_features & FEATURE_SET_LED == 0:
            return

        await self._try_command(
            "Turning the led of the miio device off failed.",
            self._device.set_led,
            False,
        )

    async def async_set_led_brightness(self, brightness: int = 2):
        """Set the led brightness."""
        if self._device_features & FEATURE_SET_LED_BRIGHTNESS == 0:
            return

        await self._try_command(
            "Setting the led brightness of the miio device failed.",
            self._device.set_led_brightness,
            AirfreshLedBrightness(brightness),
        )

    async def async_set_extra_features(self, features: int = 1):
        """Set the extra features."""
        if self._device_features & FEATURE_SET_EXTRA_FEATURES == 0:
            return

        await self._try_command(
            "Setting the extra features of the miio device failed.",
            self._device.set_extra_features,
            features,
        )

    async def async_reset_filter(self):
        """Reset the filter lifetime and usage."""
        if self._device_features & FEATURE_RESET_FILTER == 0:
            return

        await self._try_command(
            "Resetting the filter lifetime of the miio device failed.",
            self._device.reset_filter,
        )
