import json
import pip
from subprocess import Popen, PIPE
import os
import shutil
import sys
from ask_amy.cli.code_gen.code_generator import CodeGenerator
from time import sleep
import time

class DeployCLI(object):

    def create_template(self, skill_name, aws_role='', intent_schema_nm=None):
        with open(intent_schema_nm) as json_data:
             intent_schema = json.load(json_data)
        code_generator =  CodeGenerator(skill_name, aws_role, intent_schema)
        code_generator.create_cli_config()
        code_generator.create_skill_config()
        code_generator.create_skill_py()


    def create_role(self, role_name):
        base_dir = self.module_path()
        role_json = 'file://' + base_dir + '/code_gen/templates/alexa_lambda_role.json'
        iam_create_role = self.run(self.iam_create_role, role_name, role_json)
        iam_attach_policy_cloud_watch = self.run(self.iam_attach_role_policy, role_name, 'arn:aws:iam::aws:policy/CloudWatchLogsFullAccess')
        iam_attach_policy_dynamo =      self.run(self.iam_attach_role_policy, role_name, 'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess')
        response_dict = {'iam_create_role': iam_create_role,
                         'iam_attach_policy_dynamo': iam_attach_policy_dynamo,
                         'iam_attach_policy_cloud_watch': iam_attach_policy_cloud_watch}
        return json.dumps(response_dict, indent=4)

    def deploy_lambda(self, config_file_name):
        deploy_dict = self.stage_to_dist(config_file_name)
        aws_region = deploy_dict['aws_region']
        skill_name = deploy_dict['skill_name']
        lambda_zip = 'fileb://' + deploy_dict['skill_home_dir'] + '/' + deploy_dict['lambda_zip']
        aws_profile = deploy_dict['aws_profile']
        deploy_response = self.run(self.lamabda_update_function, aws_region, skill_name, lambda_zip, aws_profile)
        return json.dumps(deploy_response, indent=4)

    def create_lambda(self, config_file_name):
        deploy_dict = self.stage_to_dist(config_file_name)
        skill_name = deploy_dict['skill_name']
        lambda_runtime = deploy_dict['lambda_runtime']
        aws_role = deploy_dict['aws_role']
        lambda_handler = deploy_dict['lambda_handler']
        lambda_timeout = deploy_dict['lambda_timeout']
        lambda_memory = deploy_dict['lambda_memory']
        lambda_zip = 'fileb://' + deploy_dict['skill_home_dir'] + '/' + deploy_dict['lambda_zip']
        create_function_out = self.run(self.lambda_create_function,
                                       skill_name, lambda_runtime, aws_role, lambda_handler,
                                       skill_name, lambda_timeout, lambda_memory, lambda_zip)
        add_trigger_out = self.run(self.lambda_add_trigger, skill_name)
        response_dict = {'create_function': create_function_out, 'add_trigger': add_trigger_out}
        return json.dumps(response_dict, indent=4)

    def stage_to_dist(self, config_file_name):
        deploy_dict = self.load_json_file(config_file_name)
        skill_home_dir = deploy_dict['skill_home_dir']
        distribution_dir = skill_home_dir + '/dist'
        ask_amy_impl = None
        if 'ask_amy_dev' in deploy_dict:
            if deploy_dict['ask_amy_dev']:  # set to true
                ask_amy_home_dir = deploy_dict['ask_amy_home_dir']
                ask_amy_impl = ask_amy_home_dir + '/ask_amy'

        self.install_ask_amy(distribution_dir, ask_amy_impl)
        self.copy_skill_to_dist(skill_home_dir, distribution_dir)
        self.make_zipfile(deploy_dict['lambda_zip'], distribution_dir)
        return deploy_dict

    def log(self, log_group_name, log_stream_name=None, next_forward_token=None):
        if log_stream_name is None:
            log_stream_name = self.latest_log_stream_for_log_group(log_group_name)
        if next_forward_token is None:
            log_events_dict = self.run(self.cloudwatch_get_log_events,
                                   log_group_name, log_stream_name)
        else:
            log_events_dict = self.run(self.cloudwatch_get_log_events,
                                   log_group_name, log_stream_name, next_forward_token)
        next_forward_token = log_events_dict['nextForwardToken']
        log_events_lst = log_events_dict['events']
        for event_dict in log_events_lst:
            message = event_dict['message']
            sys.stdout.write(message)
        return next_forward_token, log_stream_name

    def latest_log_stream_for_log_group(self, log_group_name):
        log_streams_dict = self.run(self.cloudwatch_latest_log_stream, log_group_name)
        log_streams = log_streams_dict['logStreams']
        latest_stream = log_streams[-1]
        log_stream_name = latest_stream['logStreamName']
        return log_stream_name

    def log_tail(self, log_group_name):
        next_forward_token, log_stream_name = self.log(log_group_name)
        not_done = True
        try:
            while not_done:
                sleep(1)
                next_forward_token, log_stream_name = self.log(log_group_name, log_stream_name, next_forward_token)
        except KeyboardInterrupt:
            pass
        return

    def install_ask_amy(self, destination_dir, source_dir=None):
        ask_amy_dist = destination_dir + '/ask_amy'
        try:
            shutil.rmtree(ask_amy_dist, ignore_errors=True)
            if source_dir is not None:
                shutil.copytree(source_dir, ask_amy_dist)
            else:
                pip.main(['install', '--upgrade', 'ask_amy', '-t', destination_dir])
        except FileNotFoundError:
            sys.stderr.write("ERROR: path not found {}\n".format(source_dir))
            sys.exit(-1)

    def copy_skill_to_dist(self, source_dir, destination_dir):
        files = os.listdir(source_dir)
        try:
            for file in files:
                full_path = source_dir + os.sep + file
                if file.endswith(".py"):
                    shutil.copy(full_path, destination_dir)
                if file.endswith(".json"):
                    shutil.copy(full_path, destination_dir)
        except FileNotFoundError:
            sys.stderr.write("ERROR: filename not found\n")
            sys.exit(-1)

    def make_zipfile(self, output_filename, source_dir):
        output_filename = output_filename[:-4]
        shutil.make_archive(output_filename, 'zip', source_dir)

    lamabda_update_function = ('aws', '--output', 'json', 'lambda', 'update-function-code',
                               '--region', 0,
                               '--function-name', 1,
                               '--zip-file', 2,
                               '--profile', 3
                               )

    lambda_create_function = ('aws', '--output', 'json', 'lambda', 'create-function',
                              '--function-name', 0,
                              '--runtime', 1,
                              '--role', 2,
                              '--handler', 3,
                              '--description', 4,
                              '--timeout', 5,
                              '--memory-size', 6,
                              '--zip-file', 7
                              )

    lambda_add_trigger = ('aws', '--output', 'json', 'lambda', 'add-permission',
                          '--function-name', 0,
                          '--statement-id', 'alexa_trigger',
                          '--action', 'lambda:InvokeFunction',
                          '--principal', 'alexa-appkit.amazon.com'
                          )

    cloudwatch_latest_log_stream = ('aws', '--output', 'json', 'logs', 'describe-log-streams',
                                    '--log-group-name', 0,
                                    '--order-by', 'LastEventTime'
                                    )

    iam_create_role = ('aws', '--output', 'json', 'iam', 'create-role',
                       '--role-name', 0,
                       '--assume-role-policy-document', 1
                       )

    iam_attach_role_policy = ('aws', '--output', 'json', 'iam', 'attach-role-policy',
                              '--role-name', 0,
                              '--policy-arn', 1
                              )

    cloudwatch_get_log_events = ('aws', '--output', 'json', 'logs', 'get-log-events',
                                 '--log-group-name', 0,
                                 '--log-stream-name', 1,
                                 '--next-token', 2
                                 )

    def load_json_file(self, config_file_name):
        try:
            file_ptr_r = open(config_file_name, 'r')
            deploy_dict = json.load(file_ptr_r)
            file_ptr_r.close()
        except FileNotFoundError:
            sys.stderr.write("ERROR: filename not found {}\n".format(config_file_name))
            sys.exit(-1)
        return deploy_dict

    def module_path(self):
        try:
            modpath = os.path.dirname(os.path.abspath(__file__))
        except AttributeError:
            sys.stderr.write("ERROR: could not find the path to module")
            sys.exit(-1)

        # Turn pyc files into py files if we can
        if modpath.endswith('.pyc') and os.path.exists(modpath[:-1]):
            modpath = modpath[:-1]

        # Sort out symlinks
        modpath = os.path.realpath(modpath)
        return modpath

    def run(self, arg_list, *args):
        try:
            processed_args = self.process_args(arg_list, *args)
            process = Popen(processed_args, stdout=PIPE)
            out, err = process.communicate()
            out = str(out, 'utf-8')
            if not out:
                out = '{}'
            return json.loads(out)
        except Exception as e:
            sys.stderr.write("ERROR: command line error %s\n" % args)
            sys.stderr.write("ERROR: %s\n" % e)
            sys.exit(-1)


    def process_args(self, arg_tuple, *args):
        # process the arg
        arg_list = list(arg_tuple)
        for index in range(0, len(arg_list)):
            if type(arg_list[index]) == int:
                # substitue for args passed in
                if arg_list[index] < len(args):
                    arg_list[index] = args[arg_list[index]]
                # if we have more substitutions than args passed delete the extras
                else:
                    del arg_list[index - 1:]
                    break
        return arg_list
