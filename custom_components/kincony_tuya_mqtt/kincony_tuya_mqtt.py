import logging
import ssl
import time
import hmac
import hashlib
import json
import random
import paho.mqtt.client as mqtt

_LOGGER = logging.getLogger(__name__)

TUYA_MQTT_REGIONS = {
    "cn": "m1.tuyacn.com", # 中国数据中心
    "eu": "m1.tuyaeu.com", # 中欧数据中心
    "us": "m1.tuyaus.com", # 美西数据中心
    "eus": "m1-ueaz.tuyaus.com", # 美东数据中心
    "weu": "m1-weaz.tuyaeu.com", # 西欧数据中心
    "in": "m1.tuyain.com" # 印度数据中心
}

class KinconyTuyaMqttClient:
    def __init__(self, device_id, device_secret, region):
        self.device_id = device_id
        self.device_secret = device_secret
        self.region = region
        self.property_set_listener_funcs = []
        self.client = None

    def add_property_set_listener(self, func):
        self.property_set_listener_funcs.append(func)
    
    def start(self):
        client_id = f"tuyalink_{self.device_id}"
        client = mqtt.Client(protocol=mqtt.MQTTv311, client_id=client_id)
        self.client = client
        cert_path = "./custom_components/tuya_mqtt/tuya.crt"
        client.tls_set(ca_certs=cert_path, tls_version=ssl.PROTOCOL_TLSv1_2)
        client.tls_insecure_set(True)
        username, password = self.generate_username_and_password()
        client.username_pw_set(username, password=password)
        client.connect(TUYA_MQTT_REGIONS[self.region], 8883, 60)
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        if rc != 0:
            _LOGGER.error(f"connect failed, result code={rc}")
            return

        client.subscribe(f"tylink/{self.device_id}/thing/property/set")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        payload_dict = json.loads(msg.payload)
        payload_msg_id = payload_dict.get('msgId', '')
        payload_time = payload_dict.get('time', '')
        payload_data = payload_dict.get('data', {})

        for f in self.property_set_listener_funcs:
            f(payload_msg_id, payload_time, payload_data)

    def property_report(self, data, msg_id=None):
        now = int(time.time())
        if msg_id is None:
            msg_id = self.gen_msg_id()

        _LOGGER.info("property_report: msg_id=%s, time=%s, data=%s", msg_id, now, data)

        payload = json.dumps({
            "msgId": msg_id,
            "time": now,
            "data": data
        })

        self.client.publish(f"tylink/{self.device_id}/thing/property/report", payload)

    def gen_msg_id(self):
        alphanum = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        return ''.join(random.choice(alphanum) for _ in range(32))

    def generate_username_and_password(self):
        timestamp = str(int(time.time()))
        username = f"{self.device_id}|signMethod=hmacSha256,timestamp={timestamp},secureMode=1,accessType=1"
        content = f"deviceId={self.device_id},timestamp={timestamp},secureMode=1,accessType=1"
        signature = hmac.new(self.device_secret.encode(), content.encode(), hashlib.sha256).hexdigest()
        password = signature.zfill(64)
        
        return username, password