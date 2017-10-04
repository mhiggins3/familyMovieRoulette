import logging
import datetime
from ask_amy.utilities.slot_validator import Slot_Validator

logger = logging.getLogger()

VALID = 0  # Passed validation
MSG_01_TEXT = 1  # Failed Validation


class AMAZON_NUMBER(Slot_Validator):
    def is_valid_value(self, value):
        logger.debug("AMAZON_NUMBER.is_valid_value {}".format(value))
        status_code = MSG_01_TEXT
        if isinstance(value, str):
            try:
                int(value)
                status_code = VALID
            except ValueError:
                logger.debug("Failed to convert number value {}".format(value))
        return status_code

class AMAZON_TIME(Slot_Validator):
    def is_valid_value(self, value):
        status_code = MSG_01_TEXT
        if isinstance(value, str):
            if ':' in value:
                hours_str, minutes_str = value.split(':')
                try:
                    hours = int(hours_str)
                    minutes = int(minutes_str)
                    if 0 <= hours <= 23 and 0 <= minutes <= 59:
                        status_code = VALID
                except ValueError:
                    logger.debug("Value in slot not a valid AMAZON_TIME")
            elif value in ['NI', 'MO', 'AF', 'EV']:
                status_code = VALID
        return status_code
