import sys
from ask_amy.cli.cli_deploy import DeployCLI
from ask_amy.core.exceptions import ASKAmyError
import os

HELP_BLURB = (
    "ask-amy-cli provides a simple way to create, deploy and monitor "
    "your lambda functions. \nThe available commands are: \n"
    "\n"
    "  ask-amy-cli help\n"
    "  ask-amy-cli create_role --role-name <name> \n"
    "  ask-amy-cli create_template --skill-name <name> --role-name <name> --intent-schema-file <filename>\n"
    "  ask-amy-cli create_lambda --deploy-json-file <filename>\n"
    "  ask-amy-cli deploy_lambda --deploy-json-file <filename>\n"
    "  ask-amy-cli logs --log-group-name <name> [--tail-log]\n"
)
USAGE = (
    "ask-amy-cli <command> [parameters]\n"
    "To see help text, you can run:\n"
    "\n"
    "  ask-amy-cli help\n"
    "  ask-amy-cli <command> help\n"
)


class AMYCLI(object):
    COMMANDS = ['help', 'deploy_lambda', 'create_lambda', 'create_role', 'create_template', 'logs', ]

    def parse_command(self, args):

        if len(args) == 0:
            sys.stderr.write("usage: %s\n" % USAGE)
            return None

        if len(args) == 1 and str(args[0]) == 'help':
            sys.stdout.write(HELP_BLURB)
            return None

        try:
            if len(args) >= 1:
                if args[0] in AMYCLI.COMMANDS:
                    cmd = args.pop(0)
                    if len(args) >= 1:
                        return self.execute_command(cmd, args)
                    else:
                        sys.stderr.write("ERROR: expected a valid parameter\n")
                        sys.stderr.write("usage: %s\n" % USAGE)
                else:
                    sys.stderr.write("ERROR: expected a valid command\n")
                    sys.stderr.write("usage: %s\n" % USAGE)
                    return None
        except ASKAmyError as error:
            sys.stderr.write("Error: {0}\n".format(error))

    # ask-amy-cli deploy --deploy-json-file config.json
    def deploy_lambda_cmd(self, args):
        param = args.pop(0)
        expected_param = '--deploy-json-file'
        if expected_param == param:
            cli = DeployCLI()
            ret_val = cli.deploy_lambda(args[0])
        else:
            sys.stderr.write("ERROR: expected ask-amy-cli deploy_lambda --deploy-json-file <filename> \n")
            ret_val = None
        return ret_val

    #  ask-amy-cli create --deploy-json-file config.json
    def create_lambda_cmd(self, args):
        param = args.pop(0)
        expected_param = '--deploy-json-file'
        if expected_param == param:
            cli = DeployCLI()
            ret_val = cli.create_lambda(args[0])
        else:
            sys.stderr.write("ERROR: expected ask-amy-cli create_lambda --deploy-json-file <filename> \n")
            ret_val = None
        return ret_val

    #  ask-amy-cli create --deploy-json-file config.json
    def create_role_cmd(self, args):
        param = args.pop(0)
        expected_param = '--role-name'
        if expected_param == param:
            cli = DeployCLI()
            ret_val = cli.create_role(args[0])
        else:
            sys.stderr.write("ERROR: expected ask-amy-cli create_role --role-name <name> \n")
            ret_val = None
        return ret_val

    def logs_cmd(self, args):
        tail_log = '--tail-log'
        should_tail_log = False
        if tail_log in args:
            index = args.index(tail_log)
            args.pop(index)
            should_tail_log = True

        param = args.pop(0)
        expected_param = '--log-group-name'
        if expected_param == param:
            cli = DeployCLI()
            if should_tail_log:
                ret_val = cli.log_tail(args[0])
            else:
                ret_val = cli.log(args[0])
        else:
            sys.stderr.write("ERROR: expected --log-group-name paramater \n")
            ret_val = None
        return ret_val

    def create_template_cmd(self, args):
        skill_name_kw = '--skill-name'
        skill_name = None
        role_name_kw =  '--role-name'
        role_name = None
        intent_schema_kw ='--intent-schema-file'
        intent_schema = None

        params_good=False
        if skill_name_kw in args:
            index = args.index(skill_name_kw)
            skill_name = args.pop(index+1)
            params_good=True

        if role_name_kw in args:
            index = args.index(role_name_kw)
            role_name = args.pop(index+1)

        if intent_schema_kw in args:
            index = args.index(intent_schema_kw)
            intent_schema = args.pop(index+1)

        if params_good:
            cli = DeployCLI()
            ret_val = cli.create_template(skill_name, role_name, intent_schema)
        else:
            sys.stderr.write("ERROR: expected --skill-name paramater \n")
            ret_val = None
        return ret_val

    def execute_command(self, method_name, args):
        try:
            method = getattr(self, method_name + '_cmd')
            return method(args)
        except AttributeError:
            sys.stderr.write("ERROR: unable to process request {} {}\n".format(method_name, args))
            sys.exit(-1)


def main():
    amy_cli = AMYCLI()
    args = sys.argv
    args.pop(0)
    sys.exit(amy_cli.parse_command(args))


if __name__ == '__main__':
    main()
