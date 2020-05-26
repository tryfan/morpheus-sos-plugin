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

    files = (morpheus_application_yml,)

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
                mysql_details.append({'host': host_and_port[0], 'port': host_and_port[1], 'path': url_split.path[1:]})
        else:
            endpoint = str(url_split.netloc).split(':')
            mysql_details.append({'host': endpoint[0], 'port': endpoint[1], 'path': url_split.path[1:]})
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

        mysql_command = "/opt/morpheus/embedded/bin/mysql"

        config = ConfigParser.ConfigParser()
        config.read('/opt/morpheus/embedded/mysql/ops-my.cnf')

        self.get_userpass()
        os.environ['MYSQL_PWD'] = self.mysql_pass

        if self.mysql_embedded:
            mysql_socket = config.get('client', 'socket')
            dump_opts = "--skip-lock-tables --user %s -S %s morpheus" % (self.mysql_user, mysql_socket)
            command_opts = "--user %s -S %s morpheus -e " % (self.mysql_user, mysql_socket)
        else:
            dump_opts = "--skip-lock-tables --user %s -h %s -P %s %s" \
                           % (self.mysql_user, remotedb[0]['host'], remotedb[0]['port'], remotedb[0]['path'])
            command_opts = "--user %s -h %s -P %s -e " \
                           % (self.mysql_user, remotedb[0]['host'], remotedb[0]['port'])
        cmd_check_charset = """SELECT TABLE_SCHEMA TABLE_NAME, CCSA.CHARACTER_SET_NAME AS DEFAULT_CHAR_SET,
                               COLUMN_NAME, COLUMN_TYPE, C.CHARACTER_SET_NAME
                               FROM information_schema.TABLES AS T
                               JOIN information_schema.COLUMNS AS C USING (TABLE_SCHEMA, TABLE_NAME)
                               JOIN information_schema.COLLATION_CHARACTER_SET_APPLICABILITY AS CCSA
                               ON (T.TABLE_COLLATION = CCSA.COLLATION_NAME)
                               WHERE TABLE_SCHEMA=SCHEMA()
                               AND C.DATA_TYPE IN ('enum', 'varchar', 'char', 'text', 'mediumtext', 'longtext')
                               ORDER BY TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME;"""

        self.add_cmd_output("%s %s \"%s\"" % (mysql_command, command_opts, cmd_check_charset),
                            suggest_filename="mysql_morpheus_charsets")

        if not self.get_option("nodbdump"):
            sizechecksql = """select SUM(size) "total" from (select SUM(data_length + index_length) as "size"
                              FROM information_schema.tables  GROUP BY table_schema) t1;"""
            dbsizequery = self.get_command_output("%s -sN %s '%s'" % (mysql_command, command_opts, sizechecksql))
            dbsize = int(dbsizequery['output'])
            self.add_string_as_file(dbsizequery['output'], "morpheus_mysql_dbsize_in_B")

            if dbsize > 500000000:
                self._log_warn("Database exceeds 500M, please perform mysqldump manually if requested")
            else:
                mysql_dump_command = "/opt/morpheus/embedded/bin/mysqldump"

                self.add_cmd_output("%s %s" % (mysql_dump_command, dump_opts), sizelimit=500)

    def postproc(self):
        self.do_file_sub("/opt/morpheus/embedded/mysql/ops-my.cnf",
                         r"password = (.*)",
                         r"password = ***REDACTED***")
