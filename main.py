import config
import client.ditto as dc
import client.feature as feature
import paho.mqtt.client as mqtt

from device.device import Device

import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def main():
    try:
        paho_client = mqtt.Client()
        paho_client.on_connect = paho_on_connect

        if config.mqtt_username != "":
            paho_client.username_pw_set(username=config.mqtt_username, password=config.mqtt_password)

        paho_client.connect(host=config.mqtt_host, port=int(config.mqtt_port))
        paho_client.loop_forever()
    except KeyboardInterrupt:
        print("finished")
        ditto_client.disconnect()
        paho_client.disconnect()


def paho_on_connect(client, userdata, flags, rc):

    global ditto_client

    f = feature.from_yaml("feature.yaml")
    device = Device(f, config.robot_hostname, config.robot_port, config.robot_default_process_id)
    device.set_refresh_timeout(config.robot_refresh_timeout)
    ditto_client = dc.DittoClient(paho_client=client, feature=f, event_handler=device)
    f.set_change_handler(ditto_client)

    device.run()

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    ditto_client.enable_logger(True, logger)
    ditto_client.connect()


if __name__ == "__main__":
    main()
