import logging

from ask_amy.core.object_dictionary import ObjectDictionary

logger = logging.getLogger()


class Request(ObjectDictionary):
    def __init__(self, request_dict):
        super().__init__(request_dict)

    @property
    def request_type(self):
        return self.get_value_from_dict(['type'])

    @property
    def request_id(self):
        return self.get_value_from_dict(['requestId'])

    @property
    def locale(self):
        return self.get_value_from_dict(['locale'])

    @property
    def timestamp(self):
        return self.get_value_from_dict(['timestamp'])

    @property
    def attributes(self):
        has_attributes = self.get_value_from_dict(['attributes'])
        if has_attributes is None:
            self._obj_dict['attributes'] = {}
        return self._obj_dict['attributes']

    def attribute_exists(self, attribute):
        if attribute in self.attributes.keys():
            return True
        else:
            return False

    @staticmethod
    def factory(request_dict):
        logger.debug("**************** entering Request.factory")
        request_type = request_dict['type']
        if request_type == "LaunchRequest": return LaunchRequest(request_dict)
        if request_type == "IntentRequest": return IntentRequest(request_dict)
        if request_type == "SessionEndedRequest": return SessionEndedRequest(request_dict)
        assert 0, "Bad Request creation: " + request_type


class LaunchRequest(Request):
    def __init__(self, request_dict):
        super().__init__(request_dict)


class IntentRequest(Request):
    CONFIRMATION_STATUSES = ['NONE', 'CONFIRMED', 'DENIED']
    DIALOG_STATES = ['STARTED', 'IN_PROGRESS', 'COMPLETED']

    def __init__(self, request_dict):
        super().__init__(request_dict)
        self._slots = None

    @property
    def dialog_state(self):
        return self.get_value_from_dict(['dialogState'])

    @property
    def intent_name(self):
        return self.get_value_from_dict(['intent', 'name'])

    @property
    def confirmation_status(self):
        return self.get_value_from_dict(['intent', 'confirmationStatus'])

    @property
    def slots(self):
        if self._slots is None:
            self._slots = {}
            slots_dict = self.get_value_from_dict(['intent', 'slots'])
            if slots_dict is not None:
                for slot_name in slots_dict.keys():
                    self._slots[slot_name] = Slot(slots_dict[slot_name])
        return self._slots

    def value_for_slot_name(self, name):
        path = ['intent', 'slots', name, 'value']
        return self.get_value_from_dict(path)


class SessionEndedRequest(Request):
    REASONS = ['USER_INITIATED', 'ERROR', 'EXCEEDED_MAX_REPROMPTS']
    ERROR_TYPES = ['INVALID_RESPONSE', 'DEVICE_COMMUNICATION_ERROR', 'INTERNAL_ERROR']

    def __init__(self, request_dict):
        super().__init__(request_dict)

    @property
    def reason(self):
        return self.get_value_from_dict(['reason'])

    @property
    def error_type(self):
        return self.get_value_from_dict(['error', 'type'])

    @property
    def error_message(self):
        return self.get_value_from_dict(['error', 'message'])


class Slot(ObjectDictionary):
    CONFIRMATION = ['NONE', 'CONFIRMED', 'DENIED']

    def __init__(self, slot_dict):
        super().__init__(slot_dict)

    @property
    def name(self):
        return self.get_value_from_dict(['name'])

    @property
    def value(self):
        return self.get_value_from_dict(['value'])

    @property
    def confirmation_status(self):
        return self.get_value_from_dict(['confirmationStatus'])
