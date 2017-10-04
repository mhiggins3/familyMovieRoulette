import logging
import json


class ObjectDictionary(object):
    logger = logging.getLogger()

    def __init__(self, obj_dict):
        self._obj_dict = obj_dict

    def get_value_from_dict(self, path, override_dict=None):
        """
        Return a value in a dictionary given a collection of keys that
        point to the value
        :param path: a list of keys in the dictionary
        :param override_dict: a dictionary to be used if provided overriding
        the base dictionary. (This is often a sub dictionary of the base but it
        does not need to be
        :return: None or the value found
        """
        if override_dict is None:
            val = self._obj_dict
        else:
            val = override_dict
        try:
            for arg in path:
                val = val[arg]
                if val == '?':  # This ? is returned on occasion in Alexa Response
                    val = None

        except KeyError:
            # self.logger.debug("ObjectDictionary failed to find={} in dict={}".format(path, val))
            val = None
        return val

    def json(self):
        return self._obj_dict

    def __str__(self):
        return json.dumps(self._obj_dict, indent=4)
