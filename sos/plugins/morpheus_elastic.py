from sos.plugins import Plugin, RedHatPlugin, DebianPlugin, UbuntuPlugin
import os
import yaml
import datetime
import urllib3
try:
    import requests
    REQUESTS_LOADED = True
except ImportError:
    REQUESTS_LOADED = False

try:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass


class MorpheusElastic(Plugin, RedHatPlugin, DebianPlugin, UbuntuPlugin):
    """Morpheus Embedded Elasticsearch
    """
    short_desc = 'Morpheus ElasticSearch Service'
    plugin_name = 'morpheus_elastic'
    profiles = ('services', )

    es_embedded = True
    es_config_file = ""
    morpheus_application_yml = "/opt/morpheus/conf/application.yml"

    protocol = "http"
    es_user = None
    es_password = None

    files = (morpheus_application_yml,)

    def check_es_embedded(self):
        es_status_local = self.get_command_output("morpheus-ctl status elasticsearch")
        if not es_status_local['output']:
            self.es_embedded = False

    def get_remote_hostnames_ports(self):
        if os.path.isfile(self.morpheus_application_yml):
            with open(self.morpheus_application_yml) as appyml:
                appyml_data = yaml.load(appyml, Loader=yaml.Loader)
        es_hosts = []
        es_config = appyml_data['environments']['production']['elasticSearch']
        if "protocol" in es_config.keys():
            self.protocol = es_config['protocol']
        if "user" in es_config.keys():
            self.es_user = es_config['user']
        if "password" in es_config.keys():
            self.es_password = es_config['password']
        es_host_detail = es_config['client']['hosts']
        return es_host_detail

    def get_local_hostname_port(self):
        if os.path.isfile(self.morpheus_application_yml):
            with open(self.morpheus_application_yml) as appyml:
                appyml_data = yaml.load(appyml, Loader=yaml.Loader)

        es_config = appyml_data['environments']['production']['elasticSearch']
        hostname = es_config['client']['hosts'][0]['host']
        port = es_config['client']['hosts'][0]['port']
        return str(hostname), str(port)

    def get_morpheus_logs(self, endpoint):
        json_options = """
        { "sort": [ "ts" ], "query": { "match_all": {} } }
        """
        datelist = []
        today = datetime.datetime.today()
        since = self.get_option('since')
        if since is not None:
            delta = today - since
            daysback = delta.days
        else:
            daysback = 7
        for i in range(0, daysback + 1):
            datedelta = datetime.timedelta(days=i)
            moddate = today - datedelta
            datelist.append("logs." + moddate.strftime("%Y%m%d"))

        for day in datelist:
            if self.protocol == "http":
                self.add_cmd_output(
                    "curl -s -X GET '%s/%s/_search?pretty&size=10000' -H 'Content-Type: application/json' -d '%s'"
                    % (endpoint, day, json_options),
                    suggest_filename="morpheus_" + day
                )
            else:
                if REQUESTS_LOADED:
                    headers = {'Content-Type': 'application/json'}
                    req = requests.get("%s/%s/_search?pretty&size=10000"
                                       % (endpoint, day),
                                       auth=(self.es_user, self.es_password),
                                       headers=headers,
                                       json=json_options,
                                       verify=False)
                    self.add_string_as_file(req.text, "morpheus_" + day)

    def setup(self):
        self.check_es_embedded()
        if self.es_embedded:
            es_config_file = "/opt/morpheus/embedded/elasticsearch/config/elasticsearch.yml"
            self.add_copy_spec(es_config_file)

            log_base_dir = "/var/log/morpheus/elasticsearch/"
            self.add_copy_spec(es_config_file)
            self.add_copy_spec(log_base_dir + "morpheus_*.log")
            self.add_copy_spec(log_base_dir + "morpheus.log")
            self.add_copy_spec(log_base_dir + "current")

            host, port = self.get_local_hostname_port()

            endpoint = host + ":" + port
            self.add_cmd_output([
                "curl -X GET '%s/_cluster/settings?pretty'" % endpoint,
                "curl -X GET '%s/_cluster/health?pretty'" % endpoint,
                "curl -X GET '%s/_cluster/stats?pretty'" % endpoint,
                "curl -X GET '%s/_cat/nodes?v'" % endpoint,
            ])

            self.get_morpheus_logs(endpoint)
        else:
            es_hosts = self.get_remote_hostnames_ports()

            runonce = True
            for hp in es_hosts:
                if self.protocol == "http":
                    endpoint = str(hp['host']) + ":" + str(hp['port'])
                    self.add_cmd_output("curl -k -X GET '%s/_cluster/settings?pretty'" % endpoint,
                                        suggest_filename="%s_get_cluster_settings" % str(hp['host']))
                    self.add_cmd_output("curl -k -X GET '%s/_cluster/health?pretty'" % endpoint,
                                        suggest_filename="%s_get_cluster_health" % str(hp['host']))
                    self.add_cmd_output("curl -k -X GET '%s/_cluster/stats?pretty'" % endpoint,
                                        suggest_filename="%s_get_cluster_stats" % str(hp['host']))
                    self.add_cmd_output("curl -k -X GET '%s/_cat/nodes?v'" % endpoint,
                                        suggest_filename="%s_get_nodes" % str(hp['host']))
                else:
                    if REQUESTS_LOADED:
                        endpoint = self.protocol + "://" + str(hp['host']) + ":" + str(hp['port'])
                        if self.es_user and self.es_password:
                            req = requests.get(endpoint + "/_cluster/settings?pretty",
                                               verify=False,
                                               auth=(self.es_user, self.es_password))
                            self.add_string_as_file(req.text, "%s_get_cluster_settings" % str(hp['host']))
                            req = requests.get(endpoint + "/_cluster/health?pretty",
                                               verify=False,
                                               auth=(self.es_user, self.es_password))
                            self.add_string_as_file(req.text, "%s_get_cluster_health" % str(hp['host']))
                            req = requests.get(endpoint + "/_cluster/stats?pretty",
                                               verify=False,
                                               auth=(self.es_user, self.es_password))
                            self.add_string_as_file(req.text, "%s_get_cluster_stats" % str(hp['host']))
                            req = requests.get(endpoint + "/_cat/nodes?v",
                                               verify=False,
                                               auth=(self.es_user, self.es_password))
                            self.add_string_as_file(req.text, "%s_get_nodes" % str(hp['host']))
                        else:
                            req = requests.get(endpoint + "/_cluster/settings?pretty",
                                               verify=False)
                            self.add_string_as_file(req.text, "%s_get_cluster_settings" % str(hp['host']))
                            req = requests.get(endpoint + "/_cluster/health?pretty",
                                               verify=False)
                            self.add_string_as_file(req.text, "%s_get_cluster_health" % str(hp['host']))
                            req = requests.get(endpoint + "/_cluster/stats?pretty",
                                               verify=False)
                            self.add_string_as_file(req.text, "%s_get_cluster_stats" % str(hp['host']))
                            req = requests.get(endpoint + "/_cat/nodes?v",
                                               verify=False)
                            self.add_string_as_file(req.text, "%s_get_nodes" % str(hp['host']))

                if runonce:
                    self.get_morpheus_logs(endpoint)
                    runonce = False
