import requests
import json


class jira_request(object):
    __base_api3_url = "{0}/rest/api/3/{1}"
    __statuses = {}


    def __init__(self, base_url, auth_values):
        self.__base_url = base_url
        self.__auth_values = auth_values


    def __load_statuses(self):
        data = self.get_api3_request("status")
        for status in data:
            self.__statuses[status["id"]] = status["name"]


    def get_status_name(self, status_id):
        if len(self.__statuses) == 0:
            self.__load_statuses()        

        return self.__statuses.get(status_id)


    def __get_request(self, url):
        response = requests.get(url, auth=self.__auth_values)
        if response.ok:
            return json.loads(response.content)
        else:
            response.raise_for_status()


    def get_api3_request(self, url_path):
        return self.__get_request(self.__base_api3_url.format(self.__base_url, url_path))