import logging

from ask_amy.core.skill_factory import SkillFactory
from ask_amy.core.object_dictionary import ObjectDictionary
from ask_amy.database.database import DynamoDB

logger = logging.getLogger()


class Session(ObjectDictionary):
    def __init__(self, session_dict):
        super().__init__(session_dict)

        self._persistence = False  # Assume no persistence until explicitly defined
        config_dict = SkillFactory.load_configuartion(self.__class__.__name__)
        if config_dict:
            self._persistence = self.get_value_from_dict(['persistence'], config_dict)
            if self._persistence:
                self._table_name = self.get_value_from_dict(['table_name'], config_dict)
                self._fields_to_persist = self.get_value_from_dict(['fields_to_persist'], config_dict)
                if self.get_value_from_dict(['new']):  # if new session load data
                    self.load()

    @property
    def session_id(self):
        return self.get_value_from_dict(['sessionId'])

    @property
    def application_id(self):
        return self.get_value_from_dict(['application', 'applicationId'])

    @property
    def is_new_session(self):
        return self.get_value_from_dict(['new'])

    @property
    def user_id(self):
        return self.get_value_from_dict(['user', 'userId'])

    @property
    def access_token(self):
        return self.get_value_from_dict(['user', 'accessToken'])

    @property
    def consent_token(self):
        return self.get_value_from_dict(['user', 'permissions', 'consentToken'])

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

    def load(self):
        logger.debug("**************** entering Session.load")
        if self._persistence:
            dynamo_db = DynamoDB(self._table_name)
            session_data = dynamo_db.load(self.user_id)
            for name in session_data.keys():
                self.attributes[name] = session_data[name]['value']

    def save(self):
        logger.debug("**************** entering Session.save")
        if self._persistence:
            dynamo_db = DynamoDB(self._table_name)
            session_data = self.attributes
            dynamo_db.save(self.user_id, self._fields_to_persist, session_data)

    def reset_stored_values(self):
        logger.debug("**************** entering Session.reset_stored_values")
        if self._persistence:
            dynamo_db = DynamoDB(self._table_name)
            dynamo_db.update_data(self.user_id, DynamoDB.NAME, DynamoDB.SESSION_DATA, "{}")
