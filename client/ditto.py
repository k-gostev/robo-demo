from ditto.client import Client
from ditto.model.feature import Feature
from ditto.model.namespaced_id import NamespacedID
from ditto.protocol.envelope import Envelope
from ditto.protocol.things.commands import Command
from ditto.protocol.things.messages import Message


class DittoClient(Client):
    def __init__(self, feature, event_handler, *args, **kwargs):
        self.__feature__ = feature
        self.__message_handler__ = event_handler
        super().__init__(*args, **kwargs)

    def on_connect(self, ditto_client: Client):
        print("Ditto client connected")
        self.subscribe(self.on_message)
        print("subscribed")
        self.__update_feature__()

    def on_properties_change(self, properties):
        self.__update_feature__()

    def __update_feature__(self):
        cmd = Command(NamespacedID().from_string(self.__feature__.get_namespace_id()))\
            .feature(feature_id=self.__feature__.get_name())\
            .twin() \
            .modify(Feature()
                    .with_definition_from("kanto.demo:RoboDemo:1.0.0")
                    .with_properties(properties=self.__feature__.get_properties())
                    .to_ditto_dict())

        self.send(cmd.envelope(response_required=False, content_type="application/json"))
        print("Feature details sent")

    def on_disconnect(self, ditto_client: Client):
        print("Ditto client disconnected")
        self.unsubscribe(self.on_message)
        print("unsubscribed")

    def on_message(self, request_id: str, message: Envelope):
        print("request_id: {}, envelope: {}".format(request_id, message.to_ditto_dict()))

        # create an example outbox message and reply
        live_message = Message(NamespacedID().from_string(self.__feature__.get_namespace_id())).outbox(message.topic.action).with_payload(
            dict(status=self.__message_handler__.on_message(request_id, message))).feature(self.__feature__.get_name())

        # generate the respective Envelope
        response_envelope = live_message.envelope(correlation_id=message.headers.correlation_id,
                                                  response_required=False).with_status(204)
        # send the reply
        self.reply(request_id, response_envelope)
        print("reply sent")

    def on_log(self, ditto_client: Client, level, string):
        print("[{}] {}".format(level, string))
