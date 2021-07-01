import yaml


class jira_config(object):
    __jira_config_file = "jira_conf.yaml"
    __teams = {}
    __categories = {}
    __filters = {}


    def __init__(self):
        self.__load_config()


    def __load_config(self):
        with open(self.__jira_config_file, "r") as config_file:
            jira_config = yaml.safe_load(config_file)
            self.__base_url = jira_config[0]["jira"]["url"]
            self.__auth_values = jira_config[0]["jira"]["user"], jira_config[0]["jira"]["token"]
            if len(jira_config) > 1:
                self.__teams = jira_config[1]["team"]
            if len(jira_config) > 2:
                self.__categories = jira_config[2]["category"]
            if len(jira_config) > 3:
                self.__filters = jira_config[3]["filter"]


    @property
    def base_url(self):
        return self.__base_url


    @property
    def auth_values(self):
        return self.__auth_values


    def get_teams(self):
        return list(self.__teams.values())


    def find_team(self, labels):
        for label in labels:
            team = self.__teams.get(label.casefold())
            if team is not None:
                return team
        return ""


    def find_category(self, labels):
        for label in labels:
            category = self.__categories.get(label.casefold())
            if category is not None:
                return category
        return "Unknown"


    def find_filter_id(self, filter):
        return self.__filters.get(filter)

    
    def get_first_filter_id(self):
        if len(self.__filters) > 0:
            return list(self.__filters.values())[0]
        return None