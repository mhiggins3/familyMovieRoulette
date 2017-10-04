from ask_amy.core.default_dialog import DefaultDialog
from ask_amy.core.request import IntentRequest
from ask_amy.core.reply import Reply
from ask_amy.utilities.slot_validator import Slot_Validator
from ask_amy.core.exceptions import SlotValidatorLoadError
from functools import wraps
import logging
import json

logger = logging.getLogger()


class StackDialogManager(DefaultDialog):
    def no_intent(self):
        logger.debug("**************** StackDialogManager.no_intent")
        return self.confirmation_intent('no')

    def yes_intent(self):
        logger.debug("**************** StackDialogManager.yes_intent")
        return self.confirmation_intent('yes')

    def confirmation_intent(self, confirmation):
        logger.debug("**************** StackDialogManager.confirmation_intent")
        established_dialog = self.peek_established_dialog()
        state_good = True
        if established_dialog is None:
            state_good = False
        else:
            if established_dialog['intent_name'] != 'confirmation_intent':
                state_good = False

        if state_good:
            self.pop_established_dialog()
            established_dialog = self.peek_established_dialog()
            self._intent_name = established_dialog['intent_name']
            established_dialog['confirmation'] = confirmation
            return self.execute_method(self.intent_name)
        else:
            return self.handle_session_end_confused()

    def requested_value_intent(self):
        logger.debug("**************** StackDialogManager.requested_value_intent")
        # is this a good state?
        established_dialog = self.peek_established_dialog()

        if established_dialog is None:
            return self.handle_session_end_confused()
        else:
            if established_dialog['intent_name'] != self.intent_name:
                return self.handle_session_end_confused()

        not_valid_slots = self.slot_data_to_intent_attributes()
        if not_valid_slots is not None:
            self.pop_established_dialog()
            return self.need_valid_data(not_valid_slots)



        current_dialog = self.pop_established_dialog()
        if 'requested_value' not in current_dialog:
            return self.handle_session_end_confused()

        slot_name = current_dialog['slot_name']
        requested_value = current_dialog['requested_value']

        established_dialog = self.peek_established_dialog()
        established_dialog[slot_name] = requested_value
        self._intent_name = established_dialog['intent_name']
        return self.execute_method(self._intent_name)

    def redirect_to_initialize_dialog(self, intent_name):
        """
        Simple redirect. We use this if an intent is called but a prior intent was expected
        :param intent_name:
        :return:
        """
        self._intent_name = intent_name
        return self.execute_method(intent_name)

    def get_expected_intent_for_data(self, data_name):
        return self.get_value_from_dict(['slots', data_name, 'expected_intent'])

    def handle_session_end_confused(self):
        """
        Called if we are in an intent but don't have the info to move forward
        and are not sure how or why alex called us here (obviously this should not
        be a common occurrence.)
        :return:
        """
        logger.debug('**************** entering StackDialogManager.handle_session_end_confused')
        # can we re_prompt?
        MAX_RETRY = 4
        dialog_state = self.peek_established_dialog()
        if dialog_state is None:
            dialog_state = {}

        if 'retry_attempted' not in dialog_state.keys():
            dialog_state['retry_attempted'] = 1

        if dialog_state['retry_attempted'] <= MAX_RETRY:
            prompt_dict = {"speech_out_text": "Could you please repeat or say help.",
                           "should_end_session": False}

            if 'slot_name' in dialog_state.keys():
                requested_value_nm = dialog_state['slot_name']
                prompt_dict = self.get_re_prompt_for_slot_data(requested_value_nm)

            dialog_state['retry_attempted'] += 1
            return Reply.build(prompt_dict, self.event)
        else:
            # we are done
            self._intent_name = 'handle_session_end_confused'
            return self.handle_default_intent()

    def get_re_prompt_for_slot_data(self, data_name):
        slot_data_details = self.get_value_from_dict(['slots', data_name])
        if 're_prompt_text' in slot_data_details:
            slot_data_details['speech_out_text'] = slot_data_details['re_prompt_text']
            del slot_data_details['re_prompt_text']
        if 're_prompt_ssml' in slot_data_details:
            slot_data_details['speech_out_ssml'] = slot_data_details['re_prompt_ssml']
            del slot_data_details['re_prompt_ssml']
        slot_data_details['should_end_session'] = False
        return slot_data_details

    def is_good_state(self):
        """
        Checks the state of the dialog and establish a conversation if this is the first
        interaction on a multi step intent
        :return:
        """
        logger.debug('**************** entering StackDialogManager.is_good_state')
        # did the expected intent get called?
        state_good = True
        established_dialog = self.peek_established_dialog()
        if established_dialog is not None:
            if established_dialog['intent_name'] != self.intent_name:
                state_good = False
        else:
            self.push_established_dialog(self.intent_name)
        return state_good

    def peek_established_dialog(self):
        """
        peek at the current intent state
        :return:
        """
        logger.debug("**************** entering StackDialogManager.peek_established_dialog")
        intent_attributes = None
        if self.session.attribute_exists('established_dialog'):
            dialog_stack = self.session.attributes['established_dialog']
            if len(dialog_stack) > 0:
                intent_attributes = dialog_stack[len(dialog_stack) - 1]
        return intent_attributes

    def push_established_dialog(self, intent_name):
        """
        Push an intent and its state  onto the stack
        :param intent_name:
        :return:
        """
        logger.debug("**************** entering StackDialogManager.push_established_dialog")
        new_intent_attributes = {"intent_name": intent_name}
        # If we dont have an established_dialog create one
        if 'established_dialog' not in self.session.attributes.keys():
            self.session.attributes['established_dialog'] = [new_intent_attributes]
            return new_intent_attributes

        dialog_stack = self.session.attributes['established_dialog']

        # if we do have an established_dialog but no active intent_attributes add the new one
        active_intent_attributes = self.peek_established_dialog()
        if active_intent_attributes is None:
            dialog_stack.append(new_intent_attributes)
        else:
            # if we do have an established_dialog and intent_attributes
            # is the new intent different from the one I am working on?
            # if so add it otherwise just use the one that is established
            if active_intent_attributes['intent_name'] != intent_name:
                dialog_stack.append(new_intent_attributes)

        return new_intent_attributes

    def pop_established_dialog(self):
        """
        pop an intent state from the stack
        :return:
        """
        logger.debug("**************** entering StackDialogManager.pop_established_dialog")
        intent_attributes = None
        if self.session.attribute_exists('established_dialog'):
            dialog_stack = self.session.attributes['established_dialog']
            intent_attributes = dialog_stack.pop()
        return intent_attributes

    def reset_established_dialog(self):
        """
        reset the whole intent dialog stack
        :return:
        """
        logger.debug("**************** entering StackDialogManager.reset_established_dialog")
        if self.session.attribute_exists('established_dialog'):
            dialog_stack = self.session.attributes['established_dialog']
            del dialog_stack[:]

    def required_fields_process(self, required_fields):
        """
        review the required fields to process this intent if we have all the data move forward
        if not create a reply that will call an appropriate intent to get the missing data
        :param required_fields:
        :return:
        """
        logger.debug("**************** entering StackDialogManager.required_fields_process")
        reply_dict = None
        intent_attributes = self.peek_established_dialog()
        for key in required_fields:
            if key not in intent_attributes.keys():
                expected_intent = self.get_expected_intent_for_data(key)
                new_intent_attributes = self.push_established_dialog(expected_intent)
                new_intent_attributes['slot_name'] = key
                reply_slot_dict = self.get_slot_data_details(key)
                return Reply.build(reply_slot_dict, self.event)

        return reply_dict

    def get_slot_data_details(self, data_name):
        slot_data_details = self.get_value_from_dict(['slots', data_name])
        slot_data_details['should_end_session'] = False
        return slot_data_details

    def slot_data_to_intent_attributes(self):
        """
        Move slot data into intent state data. This will collect the data required to
        execute the initial intent. (i.e. similar to flow state in JSF)
        :return:
        """
        logger.debug("****************! entering StackDialogManager.slot_data_to_intent_attributes")
        # If we have an Intent Request map the slot values to the intent dialog
        validation_errors = None
        if isinstance(self.event.request, IntentRequest):
            slots_dict = self.event.request.slots
            intent_attributes = self.peek_established_dialog()
            for name in slots_dict.keys():
                # get the value for this slot name if available
                value = self.request.value_for_slot_name(name)

                if value is not None:
                    intent_attributes[name] = value

                    if name == 'requested_value' and 'slot_name' in intent_attributes:
                        name = intent_attributes['slot_name']

                    slot_validation = self.get_value_from_dict(['slots', name, 'validation'])
                    if slot_validation is not None:
                        status_code = self.is_valid_slot_data_type(name, value, slot_validation['type_validator'])
                        if status_code != 0:

                            if validation_errors is None:
                                validation_errors = []

                            validation_error = (name, status_code)
                            validation_errors.append(validation_error)

        return validation_errors

    def need_valid_data(self, validation_errors):
        logger.debug("**************** entering StackDialogManager.need_valid_data")
        for validation_error in validation_errors:
            slot_name = validation_error[0]
            status_code = validation_error[1]

            expected_intent = self.get_expected_intent_for_data(slot_name)
            new_intent_attributes = self.push_established_dialog(expected_intent)
            new_intent_attributes['slot_name'] = slot_name

            slot_details = self.get_value_from_dict(['slots', slot_name])
            slot_details['should_end_session'] = False
            msg_text = 'msg_{0:02d}_text'.format(status_code)
            slot_details['speech_out_text'] = slot_details['validation'][msg_text]
            reply = Reply.build(slot_details, self.event)
            return reply

    def required_fields_in_session_attributes_to_intent_attributes(self, required_fields):
        """
        Move session data into intent state data. This will stage the data we have already collected
        that is required to execute the intent.
        :return:
        """
        logger.debug(
            "**************** entering StackDialogManager.required_fields_in_session_attributes_to_intent_attributes")
        # If we have an Intent Request map the slot values to the session
        if isinstance(self.event.request, IntentRequest):
            intent_attributes = self.peek_established_dialog()
            for name in required_fields:
                if self.session.attribute_exists(name):
                    intent_attributes[name] = self.session.attributes[name]

    def intent_attributes_to_request_attributes(self):
        dialog_state = self.peek_established_dialog()
        for key in dialog_state.keys():
            self.request.attributes[key] = dialog_state[key]

    def is_valid_slot_data_type(self, name, value, type_validator):
        """
        Delegates to the appropriate validator if a type check is defined in the dialog_dict
        :param name:
        :param value:
        :return:
        """
        logger.debug("**************** entering StackDialogManager.is_valid_slot_data_type")
        valid = True
        if type_validator is None:
            return valid  # If type is not defined skip validation test
        else:
            try:
                if type_validator.startswith('AMAZON'):
                    type_validator = "ask_amy.utilities.iso_8601_validator.{}".format(type_validator)
                validator = Slot_Validator.class_from_str(type_validator)
                valid = validator().is_valid_value(value)
            except SlotValidatorLoadError:
                logger.debug("Unable to load {}".format(type_validator))
                # Skip validation
                valid = True
        return valid


def required_fields(fields, user_managed=False):
    """
    Required fields decorator manages the state of the intent
    :param fields:
    :param user_managed:
    :return:
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            obj = args[0]
            if isinstance(obj, StackDialogManager):
                if obj.is_good_state():
                    obj.required_fields_in_session_attributes_to_intent_attributes(fields)
                    not_valid_slots = obj.slot_data_to_intent_attributes()
                    if not_valid_slots is not None:
                        return obj.need_valid_data(not_valid_slots)

                    need_additional_data = obj.required_fields_process(fields)
                    if need_additional_data is not None:
                        return need_additional_data
                else:
                    return obj.handle_session_end_confused()

                obj.intent_attributes_to_request_attributes()
                ret_val = func(*args, **kwargs)
                if not user_managed:
                    obj.pop_established_dialog()
            else:
                ret_val = func(*args, **kwargs)
            return ret_val

        return wrapper

    return decorator


def with_confirmation():
    """
    Required fields decorator manages the state of the intent
    :return:
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            obj = args[0]
            if isinstance(obj, StackDialogManager):
                established_dialog = obj.peek_established_dialog()
                if established_dialog is None:
                    obj.push_established_dialog(obj.intent_name)
                    obj.push_established_dialog('confirmation_intent')
                    reply_dialog = obj.reply_dialog[obj.intent_name]
                    return Reply.build(reply_dialog['conditions']['confirmation'], obj.event)
                else:
                    if established_dialog['intent_name'] != obj.intent_name:
                        return obj.handle_session_end_confused()
                    if established_dialog['confirmation'] not in ['yes', 'no']:
                        return obj.handle_session_end_confused()

                    ret_val = func(*args, **kwargs)
            else:
                ret_val = func(*args, **kwargs)
            return ret_val

        return wrapper

    return decorator
