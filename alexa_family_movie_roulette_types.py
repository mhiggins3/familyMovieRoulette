from ask_amy.utilities.slot_validator import Slot_Validator
import logging
from datetime import datetime

logger = logging.getLogger()


class ADD_MOVIE_TITLE(Slot_Validator):
    VALID = 0  # Passed validation
    MSG_01_TEXT = 1  # Failed Validation

    def is_valid_value(self, value):
        status_code = ADD_MOVIE_TITLE.MSG_01_TEXT
        if isinstance(value, str):
                status_code = ADD_MOVIE_TITLE.VALID
        return status_code


class REMOVE_MOVIE_TITLE(Slot_Validator):
    VALID = 0  # Passed validation
    MSG_01_TEXT = 1  # Failed Validation

    def is_valid_value(self, value):
        status_code = REMOVE_MOVIE_TITLE.MSG_01_TEXT
        if isinstance(value, str):
                status_code = REMOVE_MOVIE_TITLE.VALID
        return status_code

