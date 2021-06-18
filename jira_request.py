import requests
import yaml
import json

jira_config_file = "jira_conf.yaml"
base_rest_url = "{0}/rest/{1}"
base_api2_url = "{0}/rest/api/2/{1}"
base_api3_url = "{0}/rest/api/3/{1}"

class jira_request(object):
    __statuses = {}


    def __init__(self):
        self.__load_config()


    def __load_config(self):
        with open(jira_config_file, "r") as config_file:
            jira_config = yaml.safe_load(config_file)[0]["jira"]
            self.__base_url = jira_config["url"]
            self.__auth_values = jira_config["user"], jira_config["token"]


    def __load_statuses(self):
        data = self.get_api3_request("status")
        for status in data:
            # print(status["id"] + ":" + status["name"])
            self.__statuses[status["id"]] = status["name"]


    def __get_request(self, url):
        response = requests.get(url, auth=self.__auth_values)
        if response.ok:
            return json.loads(response.content)
        else:
            response.raise_for_status()

    
    def get_status_name(self, status_id):
        if len(self.__statuses) == 0:
            self.__load_statuses()        

        return self.__statuses.get(status_id)


    def get_rest_request(self, url_path):
        return self.__get_request(base_rest_url.format(self.__base_url, url_path))


    def get_api2_request(self, url_path):
        return self.__get_request(base_api2_url.format(self.__base_url, url_path))


    def get_api3_request(self, url_path):
        return self.__get_request(base_api3_url.format(self.__base_url, url_path))