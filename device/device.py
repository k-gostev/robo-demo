import logging
import time
import json

from ditto.protocol.envelope import Envelope
from client.feature import Feature
from threading import Thread
import requests


class Device:
    def __init__(self, feature: Feature, hostname, port, default_program_id):
        self.__feature__ = feature
        self.__robot_hostname__ = hostname
        self.__robot_port__ = port
        self.__default_program_id__ = default_program_id
        self.__refresh_timeout__ = 10
        self.log = logging.getLogger('DEVICE')

    def on_message(self, request_id: str, message: Envelope):
        try:

            iterations = 1
            velocity = 1
            program_id = self.__default_program_id__

            self.log.info(f'MESSAGE {message.to_ditto_dict()}')
            self.log.info(f'MESSAGE VALUE {message.value}')
            self.log.info(f'MESSAGE VALUE KEYS {message.value.keys()}')

            if "iterations" in message.value.keys():
                iterations = message.value["iterations"]
            if "velocity" in message.to_ditto_dict().keys():
                velocity = message.value["velocity"]
            if "program_id" in message.value.keys():
                program_id = message.value["program_id"]

            ep = "http://" + str(self.__robot_hostname__) + ":" + str(self.__robot_port__) + \
                 "/execute/" + str(program_id) + "/" + str(iterations) + "/" + str(velocity)
            r = requests.post(ep)
            self.log.info("POST STATUS CODE " + str(r.status_code))
            self.log.info(r.headers)
            if r.status_code < 200 or r.status_code > 299:
                return "{\"status\": \" \"REQUEST FAILED " + str(r.status_code) + "\"}"

        except Exception as e:
            self.log.error(e)
            return "{\"status\": \"FAILED WITH EXCEPTION\"}"

        return '{\"status: \"SUCCESS\"}'

    def run(self):
        t = Thread(target=self.refresh_state)
        t.start()

    def get_properties_content(self, response):
        content = response.text;
        try:
            return json.loads(content)
        except:
            return content;

    def refresh_state(self):
        while True:
            try:
                r = requests.get("http://" + self.__robot_hostname__ + ":" + self.__robot_port__ + "/robot/state")
                self.log.info("STATUS CODE " + str(r.status_code))
                self.log.info(r.headers)
                if r.status_code < 200 or r.status_code > 299:
                    return

                self.__feature__.set_properties(self.get_properties_content(r))

            except KeyboardInterrupt:
                return
            except Exception as e:
                print(e)
            time.sleep(int(self.__refresh_timeout__))

    def set_refresh_timeout(self, timeout):
        self.__refresh_timeout__ = timeout
