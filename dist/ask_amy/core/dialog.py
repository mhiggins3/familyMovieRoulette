import logging

from ask_amy.core.event import Event
from ask_amy.core.exceptions import ApplicationIdError
from ask_amy.core.object_dictionary import ObjectDictionary

logger = logging.getLogger()
import json

class Dialog(ObjectDictionary):
    def __init__(self, dialog_dict=None):
        super().__init__(dialog_dict)
        self._event = None
        self._intent_name = None

        self._sc_application_id = self.get_value_from_dict(['applicationId'])

        self._sc_request_control = {
            "LaunchRequest": "launch_request",
            "IntentRequest": "intent_request",
            "SessionEndedRequest": "session_ended_request"
        }
        self._sc_intent_control = self.get_value_from_dict(['intent_control'])

    @property
    def event(self):
        return self._event

    @property
    def session(self):
        return self._event.session

    @property
    def request(self):
        return self._event.request

    @property
    def version(self):
        return self._event.version

    @property
    def application_id(self):
        return self._sc_application_id

    @property
    def intent_name(self):
        return self._intent_name

    @property
    def reply_dialog(self):
        return self._obj_dict

    def begin(self, event_dict):
        logger.debug("**************** entering Dialog.begin")

        self._event = Event(event_dict)

        # If we have and application id in our configuration see if it matches the
        # application id in the event
        if self._sc_application_id:
            if self.session.application_id != self._sc_application_id:
                raise ApplicationIdError("Invalid Application ID")

        # If we are starting a new session then call new_session_started.
        # This methods may be overridden on the skills derived class
        if self.session.is_new_session:
            self.new_session_started()


        # Get the request type from the event and execute the mapped method
        # This methods may be overridden on the skills derived class
        # Current request may be  "LaunchRequest", "IntentRequest", "SessionEndedRequest"
        request_type = self.request.request_type
        method_name = self._sc_request_control[request_type]
        return self.execute_method(method_name)

    def execute_method(self, method_name):
        method = getattr(self, method_name)
        return method()
