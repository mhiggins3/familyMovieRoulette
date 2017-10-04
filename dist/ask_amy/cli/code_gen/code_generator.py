import logging
import os.path
from ask_amy.core.exceptions import FileExistsError
logger = logging.getLogger()


class CodeGenerator(object):
    def __init__(self, skill_name, aws_role='', intent_schema=None):
        self._skill_name = skill_name
        self._aws_role = aws_role
        self._intent_schema = intent_schema
        self._method_names = []
        self._slot_names = []


    def create_cli_config(self):
        # cwd = os.getcwd()
        CLI_CONFIG='./cli_config.json'
        if os.path.isfile(CLI_CONFIG) :
            raise FileExistsError("Attempting to OVERWRITE {}".format(CLI_CONFIG))

        with open(CLI_CONFIG, 'w') as f:
            f.write('{\n')
            f.write('    "skill_name": "{}",\n'.format(self._skill_name))
            f.write('    "skill_home_dir": ".",\n')
            f.write('    "aws_region": "us-east-1",\n')
            f.write('    "aws_profile": "default",\n')
            f.write('    "aws_role": "{}",\n\n'.format(self._aws_role))
            f.write('    "lambda_runtime": "python3.6",\n'.format('',''))
            f.write('    "lambda_handler": "ask_amy.lambda_function.lambda_handler",\n')
            f.write('    "lambda_timeout": "5",\n')
            f.write('    "lambda_memory": "128",\n')
            f.write('    "lambda_zip": "alexa_skill.zip",\n\n')
            f.write('    "ask_amy_dev": false,\n')
            f.write('    "ask_amy_home_dir": ""\n')
            f.write('}\n')


    def create_skill_config(self):
        SKILL_CONFIG='./skill_config.json'

        if os.path.isfile(SKILL_CONFIG) :
            raise FileExistsError("Attempting to OVERWRITE {}".format(SKILL_CONFIG))

        with open(SKILL_CONFIG, 'w') as file_ptr:
            file_ptr.write('{\n')
            file_ptr.write('  "Skill" : {\n')
            file_ptr.write('    "version": "1.0",\n')
            file_ptr.write('    "class_name": "{}.{}",\n'.format(self._skill_name,self.class_name()))
            file_ptr.write('    "logging_level": "debug"\n')
            file_ptr.write('  },\n')
            file_ptr.write('  "Session": {\n')
            file_ptr.write('    "persistence": false\n')
            file_ptr.write('  },\n')
            file_ptr.write('  "Dialog": {\n')
            self.intent_control(file_ptr)
            self.slots(file_ptr)
            self.intent_methods(file_ptr)
            file_ptr.write('    "help_intent": {\n')
            file_ptr.write('        "method_name": "handle_default_intent",\n')
            file_ptr.write('        "speech_out_text": "help intent",\n')
            file_ptr.write('        "should_end_session": true\n')
            file_ptr.write('        }\n')
            file_ptr.write('  }\n')
            file_ptr.write('}\n')

    def class_name(self):
        name = self._skill_name.replace("_", " ")
        name = name.title()
        name = name.replace(" ", "")
        return name

    def intent_control(self,file_ptr):
        file_ptr.write('    "intent_control": {\n')

        if 'intents' in self._intent_schema:
            for intent_item in self._intent_schema['intents']:
                if 'intent' in intent_item:
                    intent_nm =intent_item['intent']
                    method_name = self.process_intent_nm(intent_nm)
                    if method_name is not None:
                        file_ptr.write('      "{}": "{}",\n'.format(intent_nm, method_name))
        file_ptr.write('      "AMAZON.HelpIntent": "help_intent",\n')
        file_ptr.write('      "AMAZON.CancelIntent": "default_cancel_intent",\n')
        file_ptr.write('      "AMAZON.StopIntent": "default_stop_intent"\n')
        file_ptr.write('    },\n')


    def method_name(self, intent_nm):
        method_nm = intent_nm[0].lower()
        for c in intent_nm[1:]:
            if c.isupper():
                method_nm += '_'+c.lower()
            else:
                method_nm += c
        return method_nm

    def process_intent_nm(self, intent_nm, for_dialog=True):
        method_nm = None
        if intent_nm.startswith('AMAZON.'):
            if intent_nm == "AMAZON.HelpIntent" or \
                            intent_nm == "AMAZON.CancelIntent" or \
                            intent_nm == "AMAZON.StopIntent":
                intent_nm = None
            else:
                intent_nm = intent_nm[7:]
        if intent_nm is not None:
            method_nm = self.method_name(intent_nm)
            if for_dialog:
                self._method_names.append(method_nm)
        return method_nm

    def slots(self, file_ptr):
        add_close_comma = False
        file_ptr.write('    "slots": {\n')
        if 'intents' in self._intent_schema:
            for intent_item in self._intent_schema['intents']:
                intent_nm =intent_item['intent']
                if 'slots' in intent_item:
                    slots =intent_item['slots']
                    for slot in slots:
                        slot_nm = slot['name']
                        if slot_nm not in self._slot_names:
                            self._slot_names.append(slot_nm)
                            method_name = self.process_intent_nm(intent_nm, for_dialog=False)
                            if add_close_comma:
                                file_ptr.write(',\n')
                            add_close_comma= True
                            file_ptr.write('      "{}":\n'.format(slot_nm))
                            file_ptr.write('            {\n')
                            file_ptr.write('               "speech_out_text": "Please provide the {}",\n'.format(slot_nm))
                            file_ptr.write('               "re_prompt_text": "Sorry I did not hear that.",\n')
                            file_ptr.write('               "expected_intent": "{}"\n'.format(method_name))
                            file_ptr.write('            }')
            file_ptr.write('\n    },\n')


    def intent_methods(self, file_ptr):
        for method_nm in self._method_names:
            file_ptr.write('    "{}": '.format(method_nm))
            file_ptr.write('{\n')
            file_ptr.write('        "speech_out_text": "you have called the {}",\n'.format(method_nm.replace("_", " ")))
            file_ptr.write('        "should_end_session": true\n')
            file_ptr.write('        },\n')


    def create_skill_py(self):
        SKILL_PY='./'+self._skill_name+'.py'

        if os.path.isfile(SKILL_PY) :
            raise FileExistsError("Attempting to OVERWRITE {}".format(SKILL_PY))

        with open(SKILL_PY, 'w') as file_ptr:
            file_ptr.write('from ask_amy.state_mgr.stack_dialog_mgr import StackDialogManager\n')
            file_ptr.write('from ask_amy.core.reply import Reply\n')
            file_ptr.write('import logging\n')
            file_ptr.write('\n')
            file_ptr.write('logger = logging.getLogger()\n')
            file_ptr.write('\n')
            file_ptr.write('class {}(StackDialogManager):\n'.format(self.class_name()))
            file_ptr.write('\n')
            self.create_intent_methods(file_ptr)


    def create_intent_methods(self,file_ptr):
        if 'intents' in self._intent_schema:
            for intent_item in self._intent_schema['intents']:
                if 'intent' in intent_item:
                    intent_nm =intent_item['intent']
                    method_name = self.process_intent_nm(intent_nm)
                    if method_name is not None:
                        file_ptr.write('    def {}(self):\n'.format(method_name))
                        file_ptr.write('        logger.debug("**************** entering {}.{}".format('
                                       'self.__class__.__name__, self.intent_name))\n')
                        file_ptr.write('        return self.handle_default_intent()\n')
                        file_ptr.write('\n')
