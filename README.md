# Hass Tuya Mqtt
Tuya integration for home assistant using KinCony IoT products
Component use for KinCony Server16 / Server-Mini Raspberry Pi controller
Let KinCony Server16 / Server-Mini controller can work with Tuya app, remote control relay and monitor digital input state by internet.


## Example
```yaml
tuya_mqtt:
  device_id: xxxx
  device_secret: xxxx
  # region: eu, us, eus, weu, in, cn
  # eu: Central Europe Data Center
  # us: US West Data Center
  # eus: US East Data Center
  # weu: Western Europe Data Center
  # in: India Data Center
  # cn: Chinese Data Center
  region: eu 
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
