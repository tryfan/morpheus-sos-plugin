from sos.plugins import Plugin, RedHatPlugin, DebianPlugin, UbuntuPlugin
from urlparse import urlparse
import os
import yaml

# try:
#     import pymysql
#     mysqlpresent = True
# except ImportError:
#     mysqlpresent = False


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

    def check_mysql_embedded(self):
        mysql_status_local = self.get_command_output("morpheus-ctl status mysql")
        if not mysql_status_local['output']:
            self.mysql_embedded = False

    def get_remote_hostnames_ports(self):
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
            self.add_cmd_output("du -s /var/opt/morpheus/mysql/*")

        if not self.get_option("nodbdump"):
            # if mysqlpresent:
            self.get_userpass()
            os.environ['MYSQL_PWD'] = self.mysql_pass
            opts = "--user %s --all-databases" % self.mysql_user
            name = "mysqldump_--all-databases"
            self.add_cmd_output("mysqldump %s" % opts, suggest_filename=name)
            # else:
            #     self._log_warn("Could not dump Morpheus MySQL DB. Install python2-mysql")

    def postproc(self):
        self.do_file_sub("/opt/morpheus/embedded/mysql/ops-my.cnf",
                         r"password = (.*)",
                         r"password = ***REDACTED***")
