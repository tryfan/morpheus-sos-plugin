from sos.plugins import Plugin, RedHatPlugin, DebianPlugin, UbuntuPlugin


class Morpheus(Plugin, RedHatPlugin, DebianPlugin, UbuntuPlugin):

    short_desc = "Morpheus UI"
    plugin_name = "morpheus"
    profiles = ('services', )

    def setup(self):
        self.add_copy_spec("/etc/morpheus/*")
        self.add_copy_spec("/opt/morpheus/version-manifest.json")
        self.add_copy_spec("/opt/morpheus/conf/application.yml")
        self.add_copy_spec("/opt/morpheus/embedded/cookbooks/chef-run.log")
        self.add_forbidden_path("/etc/morpheus/ssl/*")
        self.add_forbidden_path("/etc/morpheus/morpheus-secrets.json")
        self.add_cmd_output([
            'morpheus-ctl status'
        ])

    def postproc(self):
        self.do_file_sub("/opt/morpheus/conf/application.yml",
                         r"password: ([\"'])(?:(?=(\\?))\2.)*?\1",
                         r"password: '***REDACTED***'")

        self.do_file_sub("/etc/morpheus/morpheus.rb",
                         r"password'] = ([\"'])(?:(?=(\\?))\2.)*?\1",
                         r"password'] = '***REDACTED***'")
