from sos.plugins import Plugin, RedHatPlugin, DebianPlugin, UbuntuPlugin
from urlparse import urlparse
import os
import yaml
import ConfigParser


class Morpheus(Plugin, RedHatPlugin, DebianPlugin, UbuntuPlugin):
    """Morpheus MySQL
    """
    short_desc = "Morpheus MySQL"
    plugin_name = "morpheus_mysql"
    profiles = ('services',)
    option_list = [
        ("nodbdump", "do not dump mysql database", "", False)
    ]

    mysql_embedded = True
    mysql_config_file = ""
    morpheus_application_yml = "/opt/morpheus/conf/application.yml"
    mysql_user = ""
    mysql_pass = ""
    tmpfilen = ""

    def check_mysql_embedded(self):
        mysql_status_local = self.get_command_output("morpheus-ctl status mysql")
        if not mysql_status_local['output']:
            self.mysql_embedded = False

    def get_remote_details(self):
        if os.path.isfile(self.morpheus_application_yml):
            with open(self.morpheus_application_yml) as appyml:
                appyml_data = yaml.load(appyml, Loader=yaml.Loader)

        mysql_details = []
        mysql_url = appyml_data['environments']['production']['dataSource']['url']
        url_split = urlparse(mysql_url[5:])
        if "," in url_split.netloc:
            endpoints = str(url_split.netloc).split(',')
            for endpoint in endpoints:
                host_and_port = endpoint.split(':')
                mysql_details.append({'host': host_and_port[0], 'port': host_and_port[1]})
        else:
            endpoint = str(url_split.netloc).split(':')
            mysql_details.append({'host': endpoint[0], 'port': endpoint[1]})
        return mysql_details

    def get_userpass(self):
        if os.path.isfile(self.morpheus_application_yml):
            with open(self.morpheus_application_yml) as appyml:
                appyml_data = yaml.load(appyml, Loader=yaml.Loader)
        self.mysql_user = appyml_data['environments']['production']['dataSource']['username']
        self.mysql_pass = appyml_data['environments']['production']['dataSource']['password']

    def setup(self):
        self.check_mysql_embedded()
        if self.mysql_embedded:
            self.add_copy_spec("/opt/morpheus/embedded/mysql/my.cnf")
            self.add_copy_spec("/opt/morpheus/embedded/mysql/ops-my.cnf")
            self.add_cmd_output("find /var/opt/morpheus/mysql")
            self.add_cmd_output("du -sh /var/opt/morpheus/mysql/*")
        else:
            remotedb = self.get_remote_details()

        if not self.get_option("nodbdump"):
            # if mysqlpresent:
            config = ConfigParser.ConfigParser()
            config.read('/opt/morpheus/embedded/mysql/ops-my.cnf')
            mysql_socket = config.get('client', 'socket')
            self.get_userpass()
            os.environ['MYSQL_PWD'] = self.mysql_pass
            # Check size of current DB
            sizechecksql = """select SUM(size) "total" from (select SUM(data_length + index_length) as "size"
                              FROM information_schema.tables  GROUP BY table_schema) t1;"""
            command = "/opt/morpheus/embedded/bin/mysql"
            if self.mysql_embedded:
                opts = "--user %s -S %s morpheus -sN -e '%s'" % (self.mysql_user, mysql_socket, sizechecksql)
            else:
                opts = "--user %s -h %s -P %s -sN -e '%s'" \
                       % (self.mysql_user, remotedb[0]['host'], remotedb[0]['port'], sizechecksql)
            dbsizequery = self.get_command_output("%s %s" % (command, opts))
            dbsize = int(dbsizequery['output'])

            if dbsize > 500000000:
                self._log_warn("Database exceeds 500M, please perform mysqldump manually if requested")
            else:
                command = "/opt/morpheus/embedded/bin/mysqldump"
                if self.mysql_embedded:
                    opts = "--skip-lock-tables --user %s -S %s morpheus" % (self.mysql_user, mysql_socket)
                else:
                    opts = "--skip-lock-tables --user %s -h %s -P %s" \
                           % (self.mysql_user, remotedb[0]['host'], remotedb[0]['port'])
                self.add_cmd_output("%s %s" % (command, opts), sizelimit=500)
        # else:
        #     self.get_remote_details()
        #     self.get_userpass()

    def postproc(self):
        self.do_file_sub("/opt/morpheus/embedded/mysql/ops-my.cnf",
                         r"password = (.*)",
                         r"password = ***REDACTED***")
