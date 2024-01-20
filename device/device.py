import logging
import time
import json
import config
import threading
import datetime

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

            base = BaseClient(DeviceConnection.create_tcp_connection())

            # Obtain sequences
            sequence_list = base.ReadAllSequences()
            sequence_handle = None

            for sequence in sequence_list.sequence_list:
                if sequence.name == SEQUENCE_NAME:
                    sequence_handle = sequence.handle

            if sequence_handle is None:
                self.log.error("Can't reach sequence")
                return "{\"status\": \" \"REQUEST FAILED " + "Can't reach sequence" + "\"}"

            e = threading.Event()
            notification_handle = base.OnNotificationActionTopic(
                Device.check_for_sequence_end_or_abort(e),
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

        def check(notification, e=e):
            event_id = notification.event_identifier
            task_id = notification.task_index
            if event_id == Base_pb2.SEQUENCE_TASK_COMPLETED:
                self.log.info("Sequence task {} completed".format(task_id))
            elif event_id == Base_pb2.SEQUENCE_ABORTED:
                self.log.error("Sequence aborted with error {}:{}".format(notification.abort_details,
                                                                 Base_pb2.SubErrorCodes.
                                                                 Name(notification.abort_details)))
                e.set()
            elif event_id == Base_pb2.SEQUENCE_COMPLETED:
                self.log.info("Sequence completed.")
                e.set()

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
                session_info.username = config.robot_username
                session_info.password = config.robot_password
                session_info.session_inactivity_timeout = 60000  # (milliseconds)
                session_info.connection_inactivity_timeout = 2000  # (milliseconds)
                error_callback = lambda kException: \
                    self.log.error("_________ callback error _________ {}".format(kException))
                transport = UDPTransport()
                router = RouterClient(transport, error_callback)
                transport.connect(config.robot_hostname, config.robot_port_udp)

                self.log.info("Creating session for communication")
                session_manager = SessionManager(router)
                session_manager.CreateSession(session_info)
                self.log.info("Session created")

                # Call some RPC which requires a session
                cyclic = BaseCyclicClient(router)
                feedback = cyclic.RefreshFeedback()

                session_manager.CloseSession()
                transport.disconnect()


                content = {
                    'joints': {
                        'angle': [10, 45, 70, 107, 30, 240],
                        'velocity': [4.5, 2, 8, 3.6, 5.1, 7.9],
                        'torque': [feedback.actuator[0].torque,
                                   feedback.actuator[1].torque, feedback.actuator[2].torque,
                                   feedback.actuator[3].torque, feedback.actuator[4].torque,
                                   feedback.actuator[5].torque],
                        'power': [3.5, 5, 8, 6.6, 7.1, 5.9],
                        'temperature': [-5, 15, 30, 50, 65, 75]
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
                    'mode': 1,
                    'state': 'WAITING',
                    'bastionConnection': {
                        'status': '',
                        'secondsConnected': 0
                    },
                    'system': {
                        'clock': datetime.now().isoformat()
                    }
                }

                self.__feature__.set_properties(self.get_properties_content(content))

            except KeyboardInterrupt:
                return
            except Exception as e:
                self.log.info(e)
            time.sleep(int(self.__refresh_timeout__))

    def set_refresh_timeout(self, timeout):
        self.__refresh_timeout__ = timeout


class DeviceConnection:
    TCP_PORT = 10000

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
