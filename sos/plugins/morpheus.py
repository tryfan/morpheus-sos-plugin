from sos.plugins import Plugin, RedHatPlugin, DebianPlugin, UbuntuPlugin


class Morpheus(Plugin, RedHatPlugin, DebianPlugin, UbuntuPlugin):
    """Morpheus UI
    """
    short_desc = "Morpheus UI"
    plugin_name = "morpheus"
    profiles = ('services', )

    packages = ('morpheus-appliance',)

    def setup(self):
        self.add_copy_spec("/etc/morpheus/*")
        self.add_copy_spec("/opt/morpheus/version-manifest.json")
        self.add_copy_spec("/opt/morpheus/conf/application.yml")
        self.add_copy_spec("/opt/morpheus/conf/logback.groovy")
        self.add_copy_spec("/opt/morpheus/conf/check-server-config.groovy")
        self.add_copy_spec("/opt/morpheus/embedded/cookbooks/chef-run.log")
        self.add_copy_spec("/var/log/morpheus/morpheus-ui/current")
        self.add_forbidden_path("/etc/morpheus/ssl/*")
        self.add_forbidden_path("/etc/morpheus/morpheus-secrets.json")
        self.add_cmd_output([
            'morpheus-ctl status',
            'find /opt/morpheus',
            'du -sh /opt/morpheus/*',
            'du -sh /var/opt/morpheus/*'
        ])

    def postproc(self):
        self.do_file_sub("/opt/morpheus/conf/application.yml",
                         r"password: ([\"'])(?:(?=(\\?))\2.)*?\1",
                         r"password: '***REDACTED***'")

        self.do_file_sub("/opt/morpheus/conf/application.yml",
                         r"password: ['\"]{0}(?P<password>[^\n,'\"]+)['\"]{0}",
                         r"password: ***REDACTED***")

        self.do_file_sub("/etc/morpheus/morpheus.rb",
                         r"password'] = ([\"'])(?:(?=(\\?))\2.)*?\1",
                         r"password'] = '***REDACTED***'")
