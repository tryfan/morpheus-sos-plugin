from sos.plugins import Plugin, RedHatPlugin, DebianPlugin, UbuntuPlugin
from urlparse import urlparse
import os
import yaml
import ConfigParser
from datetime import date

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
            self.add_cmd_output("du -sh /var/opt/morpheus/mysql/*")

            if not self.get_option("nodbdump"):
                # if mysqlpresent:
                config = ConfigParser.ConfigParser()
                config.read('/opt/morpheus/embedded/mysql/ops-my.cnf')
                mysql_socket = config.get('client', 'socket')
                self.get_userpass()
                os.environ['MYSQL_PWD'] = self.mysql_pass
                ### Check size of current DB
                sizechecksql = """select SUM(size) "total" from (select SUM(data_length + index_length) as "size"
                                  FROM information_schema.tables  GROUP BY table_schema) t1;"""
                command = "/opt/morpheus/embedded/bin/mysql"
                opts = "--user %s -S %s morpheus -sN -e '%s'" % (self.mysql_user, mysql_socket, sizechecksql)
                dbsizequery = self.get_command_output("%s %s" % (command, opts))
                dbsize = int(dbsizequery['output'])
                stat = os.statvfs('/tmp')
                tmpsize = stat.f_frsize * stat.f_bfree
                tmpfilen = "/tmp/morpheusdb.%s.sql" % date.today().strftime("%Y%m%d")
                if tmpsize > dbsize:
                    command = "/opt/morpheus/embedded/bin/mysqldump"
                    opts = "--user %s -S %s --all-databases" % (self.mysql_user, mysql_socket)
                    # name = "mysqldump_--all-databases"
                    outstatus = self.get_command_output("%s %s > %s" % (command, opts, tmpfilen))
                    if outstatus['status'] != 0:
                        self._log_warn("error with mysqldump: %s" % outstatus['output'])
                else:
                    self._log_warn("Not enough space in /tmp for mysqldump")

    def postproc(self):
        self.do_file_sub("/opt/morpheus/embedded/mysql/ops-my.cnf",
                         r"password = (.*)",
                         r"password = ***REDACTED***")
