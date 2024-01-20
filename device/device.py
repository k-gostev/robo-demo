import logging
import time
import json
import traceback


import config
import threading
from datetime import datetime

from client.feature import Feature

from ditto.protocol.envelope import Envelope

from kortex_api.autogen.client_stubs.BaseClientRpc import BaseClient
from kortex_api.autogen.client_stubs.BaseCyclicClientRpc import BaseCyclicClient
from kortex_api.autogen.messages import Session_pb2, Base_pb2, BaseCyclic_pb2
from kortex_api.TCPTransport import TCPTransport
from kortex_api.RouterClient import RouterClient, RouterClientSendOptions
from kortex_api.SessionManager import SessionManager
from kortex_api.autogen.messages import Session_pb2
from kortex_api.UDPTransport import UDPTransport
from kortex_api.autogen.messages.Common_pb2 import ArmState


TIMEOUT_DURATION = 30
SEQUENCE_NAME = "BOSCHSleep"


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

            device_conn = DeviceConnection(config.robot_hostname, credentials=(config.robot_username,
                                                                              config.robot_password))

            with device_conn as router:
                base = BaseClient(router)
                # Obtain sequences
                sequence_list = base.ReadAllSequences()
                sequence_handle = None

                if program_id == 1:
                    sequence_name = "BoschRedCubes"
                if program_id == 2:
                    sequence_name = "BoschGreenCubes"
                if program_id == 3:
                    sequence_name = "BoschBlueCubes"
                if program_id == 4:
                    sequence_name = "BOSCHSleep"

                for sequence in sequence_list.sequence_list:
                    if sequence.name == sequence_name:
                        sequence_handle = sequence.handle

                self.log.info(sequence_list)

                if sequence_handle is None:
                    self.log.error("Can't reach sequence")
                    return "{\"status\": \" \"REQUEST FAILED " + "Can't reach sequence" + "\"}"

                e = threading.Event()
                notification_handle = base.OnNotificationSequenceInfoTopic(
                    self.check_for_sequence_end_or_abort(e),
                    Base_pb2.NotificationOptions()
                )

                base.PlaySequence(sequence_handle)

                # Leave time to action to complete
                finished = e.wait(TIMEOUT_DURATION)
                base.Unsubscribe(notification_handle)

                if not finished:
                    print("Timeout on action notification wait")
                    return "{\"status\": \" \"REQUEST FAILED " + "Timeout" + "\"}"

        except Exception as e:
            self.log.error(e)
            return "{\"status\": \"FAILED WITH EXCEPTION\"}"

        return '{\"status: \"SUCCESS\"}'

    # Create closure to set an event after an END or an ABORT
    def check_for_sequence_end_or_abort(self, e):
        """Return a closure checking for END or ABORT notifications on a sequence

        Arguments:
        e -- event to signal when the action is completed
            (will be set when an END or ABORT occurs)
        """

        def check(notification, event=e):
            event_id = notification.event_identifier
            task_id = notification.task_index
            if event_id == Base_pb2.SEQUENCE_TASK_COMPLETED:
               pass
               # self.log.info("Sequence task {} completed".format(task_id))
            elif event_id == Base_pb2.SEQUENCE_ABORTED:
                # self.log.error("Sequence aborted with error {}:{}".format(notification.abort_details,
                #                                                  Base_pb2.SubErrorCodes.
                #                                                  Name(notification.abort_details)))
                event.set()
            elif event_id == Base_pb2.SEQUENCE_COMPLETED:
                self.log.info("Sequence completed.")
                event.set()

        return check

    def run(self):
        t = threading.Thread(target=self.refresh_state)
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
                session_info = Session_pb2.CreateSessionInfo()
                session_info.username = config.robot_username_metrics
                session_info.password = config.robot_password_metrics
                session_info.session_inactivity_timeout = 60000  # (milliseconds)
                session_info.connection_inactivity_timeout = 2000  # (milliseconds)
                error_callback = lambda kException: \
                    self.log.error("_________ callback error _________ {}".format(kException))
                # self.log.info("Creating transport")
                transport = UDPTransport()
                router = RouterClient(transport, error_callback)
                transport.connect(config.robot_hostname, int(config.robot_port_udp))

                # self.log.info("Creating session for communication")
                session_manager = SessionManager(router)
                session_manager.CreateSession(session_info)
                # self.log.info("Session created")

                # Call some RPC which requires a session
                cyclic = BaseCyclicClient(router)
                feedback = cyclic.RefreshFeedback()
                # self.log.info("feedback received {}".format(feedback))
                session_manager.CloseSession()
                transport.disconnect()
                torque = []
                angle = []
                temperature = []
                power = []
                velocity = []
                for a in feedback.actuators:
                    angle.append(round(a.position, 1))
                    temperature.append(round(a.temperature_motor, 1))
                    power.append(round(a.voltage, 1))
                    try:
                        velocity.append(round(a.velocity, 1))
                    except KeyError:
                        velocity.append(0)
                    if a.torque < 0:
                        torque.append(round(a.torque, 1)*-1)
                    else:
                        torque.append(round(a.torque, 1))

                content = {
                    'joints': {
                        'angle': angle,
                        'velocity': velocity,
                        'torque': torque,
                        'power': power,
                        'temperature': temperature
                    },
                    'position': {
                        'robotSpace': {
                            'XYZRPW': None
                        },
                        'taskSpace': {
                            'XYZRPW': None
                        }
                    },
                    'enabled': False,
                    'mastered': False,
                    'hasErrors': False,
                    'safety': {
                        'emergencyStopTP': False,
                        'emergencyStopExt': False,
                        'safeguardStop': False,
                        'dmsEngaged': False
                    },
                    'mode': round(feedback.base.arm_voltage * feedback.base.arm_current, 1),
                    'state': "{}".format(ArmState.Name(feedback.base.active_state)),
                    'bastionConnection': {
                        'status': '',
                        'secondsConnected': 0
                    },
                    'system': {
                        'clock': datetime.now().isoformat()
                    }
                }

                self.__feature__.set_properties(content)
                self.log.info("Feedback sent: {}".format(content))
            except KeyboardInterrupt:
                return
            except Exception as e:
                self.log.exception("Exception received", e)
            time.sleep(int(self.__refresh_timeout__))

    def set_refresh_timeout(self, timeout):
        self.__refresh_timeout__ = timeout


class DeviceConnection:
    TCP_PORT = 10000

    def __init__(self, ip_address, port=TCP_PORT, credentials=("", "")):
        self.ipAddress = ip_address
        self.port = port
        self.credentials = credentials

        self.sessionManager = None

        # Setup API
        self.transport = TCPTransport() if port == DeviceConnection.TCP_PORT else UDPTransport()
        self.router = RouterClient(self.transport, RouterClient.basicErrorCallback)

    @staticmethod
    def create_tcp_connection():
        """
        returns RouterClient required to create services and send requests to device or sub-devices,
        """

        return DeviceConnection(config.robot_hostname, port=config.robot_port, credentials=(config.robot_username,
                                                                                            config.robot_password))

    # Called when entering 'with' statement
    def __enter__(self):

        self.transport.connect(self.ipAddress, self.port)

        if (self.credentials[0] != ""):
            session_info = Session_pb2.CreateSessionInfo()
            session_info.username = self.credentials[0]
            session_info.password = self.credentials[1]
            session_info.session_inactivity_timeout = 10000  # (milliseconds)
            session_info.connection_inactivity_timeout = 2000  # (milliseconds)

            self.sessionManager = SessionManager(self.router)
            print("Logging as", self.credentials[0], "on device", self.ipAddress)
            self.sessionManager.CreateSession(session_info)

        return self.router

    # Called when exiting 'with' statement
    def __exit__(self, exc_type, exc_value, traceback):

        if self.sessionManager != None:
            router_options = RouterClientSendOptions()
            router_options.timeout_ms = 1000

            self.sessionManager.CloseSession(router_options)

        self.transport.disconnect()
