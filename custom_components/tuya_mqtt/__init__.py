from __future__ import annotations

from datetime import timedelta

import logging
import async_timeout
import voluptuous as vol

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers import config_validation as cv
from .tuya_mqtt import TuyaMqttClient

DOMAIN = "tuya_mqtt"

_LOGGER = logging.getLogger(__name__)

CONF_DEVICE_ID = "device_id"
CONF_DEVICE_SECRET = "device_secret"
CONF_REGION = "region"
CONF_TUYA_SWITCH = "tuya_switch"
CONF_TUYA_BINARY_SENSOR = "tuya_binary_sensor"
CONF_BIND_ID = "bind_id"
CONF_DP_KEY_RW = "dp_key_rw"
CONF_DP_KEY_R = "dp_key_r"
CONF_DP_KEY_W = "dp_key_w"
CONF_DP_KEY = "dp_key"
CONF_DP_VAL = "dp_val"
CONF_TRIGGER_STATE = "trigger_state"

# Define schemas
SWITCH_DP_KEY_R_SCHEMA = vol.Schema({
    vol.Required(CONF_DP_KEY): cv.string,
    vol.Required(CONF_DP_VAL): cv.boolean,
    vol.Required(CONF_TRIGGER_STATE): cv.boolean,
})

SWITCH_SCHEMA = vol.Schema({
    vol.Required(CONF_BIND_ID): cv.string,
    vol.Required(CONF_DP_KEY_RW): cv.string,
    vol.Optional(CONF_DP_KEY_R, default=[]): vol.All(cv.ensure_list, [SWITCH_DP_KEY_R_SCHEMA]),
})

BINARY_SENSOR_SCHEMA = vol.Schema({
    vol.Required(CONF_BIND_ID): cv.string,
    vol.Required(CONF_DP_KEY_W): cv.string,
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Required(CONF_DEVICE_SECRET): cv.string,
        vol.Required(CONF_REGION): vol.In(["cn", "eu", "us", "eus", "weu", "in"]),
        vol.Optional(CONF_TUYA_SWITCH, default=[]): vol.All(cv.ensure_list, [SWITCH_SCHEMA]),
        vol.Optional(CONF_TUYA_BINARY_SENSOR, default=[]): vol.All(cv.ensure_list, [BINARY_SENSOR_SCHEMA]),
    })
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass, config):
    """Config entry example."""
    conf = config.get(DOMAIN)
    if conf is None:
        return False

    device_id = conf["device_id"]
    device_secret = conf["device_secret"]
    region = conf["region"]
    tuya_switches = conf.get(CONF_TUYA_SWITCH, [])
    tuya_binary_sensors = conf.get(CONF_TUYA_BINARY_SENSOR, [])
    tuya_mqtt_client = TuyaMqttClient(device_id, device_secret, region)

    bind_entity_ids = []
    tuya_bind_switch_dict = {}
    tuya_bind_binary_sensor_dict = {}

    for switch in tuya_switches:
        bind_id = switch[CONF_BIND_ID]
        tuya_bind_switch_dict[bind_id] = switch
        bind_entity_ids.append(bind_id)
        
    for binary_sensor in tuya_binary_sensors:
        bind_id = binary_sensor[CONF_BIND_ID]
        tuya_bind_binary_sensor_dict[bind_id] = binary_sensor
        bind_entity_ids.append(bind_id)

    @callback
    def state_change_listener(event):
        """Handle the target switch state changes."""
        entity_id = event.data.get('entity_id')
        old_state = event.data.get('old_state')
        new_state = event.data.get('new_state')
        if new_state is None:
            return

        if old_state != None and old_state.state == new_state.state:
            return

        if entity_id in tuya_bind_switch_dict:
            bind_switch = tuya_bind_switch_dict[entity_id]
            dp_key = bind_switch['dp_key_rw']
            if new_state.state == "on":
                tuya_mqtt_client.property_report({
                    dp_key: True
                })
            elif new_state.state == "off":
                tuya_mqtt_client.property_report({
                    dp_key: False
                })
        elif entity_id in tuya_bind_binary_sensor_dict:
            bind_binary_sensor = tuya_bind_binary_sensor_dict[entity_id]
            dp_key = bind_binary_sensor['dp_key_w']
            if new_state.state == "on":
                tuya_mqtt_client.property_report({
                    dp_key: True
                })
            elif new_state.state == "off":
                tuya_mqtt_client.property_report({
                    dp_key: False
                })

            return

    # 注册监听器
    async_track_state_change_event(hass, bind_entity_ids, state_change_listener)

    def mqtt_property_set_listener(payload_msg_id, payload_time, payload_data):
        _LOGGER.info("mqtt_property_set_listener: msg_id=%s, time=%s, data=%s", 
            payload_msg_id, payload_time, payload_data)

        for switch in tuya_switches:
            bind_entity_id = switch[CONF_BIND_ID]
            dp_key_rw = switch[CONF_DP_KEY_RW]

            if dp_key_rw in payload_data:
                if payload_data[dp_key_rw]:
                    hass.services.call(
                        'switch', 'turn_on', {'entity_id': bind_entity_id}
                    )
                else:
                    hass.services.call(
                        'switch', 'turn_off', {'entity_id': bind_entity_id}
                    )

            dp_key_rs = switch.get(CONF_DP_KEY_R, [])

            for dp_key_r in dp_key_rs:
                if dp_key_r['dp_key'] in payload_data:
                    if dp_key_r['dp_val'] == payload_data[dp_key_r['dp_key']]:
                        if dp_key_r['trigger_state']:
                            hass.services.call(
                                'switch', 'turn_on', {'entity_id': bind_entity_id}
                            )
                        else:
                            hass.services.call(
                                'switch', 'turn_off', {'entity_id': bind_entity_id}
                            )

    tuya_mqtt_client.add_property_set_listener(mqtt_property_set_listener)

    tuya_mqtt_client.start()

    return True
