# Hass Tuya Mqtt

## Example
```yaml
tuya_mqtt:
  device_id: xxxx
  device_secret: xxxx
  region: cn
  tuya_switch:
    - bind_id: switch.kitchen_light
      dp_key_rw: output1
      dp_key_r:
        - dp_key: all_on
          dp_val: true
          trigger_state: on
        - dp_key: all_off
          dp_val: true
          trigger_state: off
    - bind_id: switch.bedroom_light
      dp_key_rw: output2
      dp_key_r:
        - dp_key: all_on
          dp_val: true
          trigger_state: on
        - dp_key: all_off
          dp_val: true
          trigger_state: off
  tuya_binary_sensor:
    - bind_id: binary_sensor.camera_person_detect
      dp_key_w: input3
```