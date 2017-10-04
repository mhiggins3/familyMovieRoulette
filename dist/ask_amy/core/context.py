import logging

from ask_amy.core.object_dictionary import ObjectDictionary

logger = logging.getLogger()


class Context(ObjectDictionary):
    def __init__(self, context_dict):
        super().__init__(context_dict)
        self._system = System(context_dict['System'])
        if 'AudioPlayer' in context_dict:
            self._audio_player = AudioPlayer(context_dict['AudioPlayer'])

    @property
    def system(self):
        return self._system

    @property
    def audio_player(self):
        return self._audio_player


class System(ObjectDictionary):
    def __init__(self, request_dict):
        super().__init__(request_dict)

    @property
    def api_endpoint(self):
        return self.get_value_from_dict(['apiEndpoint'])

    @property
    def application_id(self):
        return self.get_value_from_dict(['application', 'applicationId'])

    @property
    def user_id(self):
        return self.get_value_from_dict(['user', 'userId'])

    @property
    def user_access_token(self):
        return self.get_value_from_dict(['user', 'accessToken'])

    @property
    def consent_token(self):
        return self.get_value_from_dict(['user', 'permissions', 'consentToken'])

    @property
    def device_id(self):
        return self.get_value_from_dict(['device', 'deviceId'])

    @property
    def supported_interfaces(self):
        return self.get_value_from_dict(['device', 'supportedInterfaces'])


class AudioPlayer(ObjectDictionary):
    PLAYER_ACTIVITIES = ['IDLE', 'PAUSED', 'PLAYING', 'BUFFER_UNDERRUN', 'FINISHED', 'STOPPED']

    def __init__(self, request_dict):
        super().__init__(request_dict)

    @property
    def token(self):
        return self.get_value_from_dict(['token'])

    @property
    def offset_in_milliseconds(self):
        ret_val = self.get_value_from_dict(['offsetInMilliseconds'])
        # convert to int and default to 0
        return ret_val

    @property
    def player_activity(self):
        return self.get_value_from_dict(['playerActivity'])
