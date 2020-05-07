from sos.plugins import Plugin, RedHatPlugin, DebianPlugin, UbuntuPlugin
import os
# import socket
import yaml
from sos import utilities


class MorpheusRabbitMQ(Plugin, RedHatPlugin, DebianPlugin, UbuntuPlugin):

    short_desc = 'Morpheus RabbitMQ Service'
    plugin_name = 'morpheus_rabbitmq'
    profiles = ('services',)

    rmq_embedded = True
    rmq_config_file = ""
    morpheus_application_yml = "/opt/morpheus/conf/application.yml"

    def check_rmq_embedded(self):
        rmq_status_local = self.collect_cmd_output("morpheus-ctl status rabbitmq")
        if not rmq_status_local['output']:
            self.rmq_embedded = False

    def get_remote_hostnames_ports(self):
        if os.path.isfile(self.morpheus_application_yml):
            with open(self.morpheus_application_yml) as appyml:
                appyml_data = yaml.load(appyml, Loader=yaml.FullLoader)

        rmq_details = []
        rmq_config = appyml_data['environments']['production']['rabbitmq']['connectionFactories']
        for factory in rmq_config:
            rmq_details.append(factory)
        return rmq_details

    def setup(self):

        self.check_rmq_embedded()
        if self.rmq_embedded:
            original_env = os.environ
            envopts = {
                # 'HOME': '/opt/morpheus/embedded/rabbitmq',
                'PREPATH': '/opt/morpheus/bin:/opt/morpheus/embedded/bin:/opt/morpheus/embedded/sbin',
                'ERL_EPMD_ADDRESS': '127.0.0.1',
                'RABBITMQ_CONF_ENV_FILE': '/opt/morpheus/embedded/rabbitmq/etc/rabbitmq-env.conf',
                'RABBITMQ_SYS_PREFIX': '/opt/morpheus/embedded/rabbitmq',
                'RABBITMQ_CONFIG_FILE': '/opt/morpheus/embedded/rabbitmq/etc/rabbit',
                'RABBITMQ_MNESIA_BASE': '/var/opt/morpheus/rabbitmq/db',
                'RABBITMQ_SCHEMA_DIR': '/opt/morpheus/embedded/rabbitmq/priv/schema',
                'RABBITMQ_ENABLED_PLUGINS_FILE': '/opt/morpheus/embedded/rabbitmq/etc/enabled_plugins',
                'RABBITMQ_LOG_BASE': '/var/log/morpheus/rabbitmq',
                'RABBITMQ_NODE_IP_ADDRESS': '127.0.0.1',
                'RABBITMQ_NODE_PORT': '5672',
                'RABBITMQ_PID_FILE': '/var/run/morpheus/rabbitmq/rabbit@localhost.pid',
                'RABBITMQ_NODENAME': 'rabbit@localhost'
            }
            envopts['PATH'] = envopts['PREPATH'] + ":" + os.environ['PATH']
            os.environ.update(envopts)
            #envopts = {'HOME': '/opt/morpheus/embedded/rabbitmq'}
            #self.add_cmd_output("rabbitmqctl report")
            out = utilities.sos_get_command_output("rabbitmqctl report")
            self.add_string_as_file(out['output'], "rabbitmqctl_report_out")
            os.environ = original_env

            self.add_copy_spec([
                "/opt/morpheus/embedded/rabbitmq/etc/*",
                "/etc/security/limits.d/",
                "/etc/systemd/"
            ])
            self.add_copy_spec([
                "/var/log/morpheus/rabbitmq/*",
            ])

        # else:
        #     # sockettest = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #     rmq_endpoints = self.get_remote_hostnames_ports()
        #     localhosts = ['127.0.0.1', 'localhost']
        #     if any(s in rmq_endpoints[0]['hostname'] for s in localhosts):
        #         out = utilities.sos_get_command_output("rabbitmqctl report")
        #         if out['status'] is not 0:
        #             for line in out['output']:
        #                 if "mismatch" in line:
        #                     quote_split = line.split('"')
        #                     real_rabbitmq = quote_split[1]
        #             self.add_string_as_file(real_rabbitmq, "rabbit_nodename")
        #             out = utilities.sos_get_command_output("rabbitmqctl report",
        #                                                    env={'RABBITMQ_NODENAME': real_rabbitmq})
        #     self.add_string_as_file(out['output'], "rabbitmqctl_report_out")
