import yaml


class jira_config(object):
    __jira_config_file = "jira_conf.yaml"
    __teams = {}
    __categories = {}
    __category_colours = {}
    __filters = {}
    __status_colours = {}


    def __init__(self, config_file = None):
        if config_file:
            self.__jira_config_file = config_file
        self.__load_config()


    def __load_config(self):
        with open(self.__jira_config_file, "r") as config_file:
            jira_config = yaml.safe_load(config_file)

            self.__base_url = jira_config["jira"]["url"]
            self.__auth_values = jira_config["jira"]["user"], jira_config["jira"]["token"]

            try:
                self.__teams = jira_config["team"]
            except KeyError:
                pass
            try:
                self.__load_category_config(jira_config["category"])
            except KeyError:
                pass
            try:
                self.__status_colours = jira_config["status"]
            except KeyError:
                pass
            try:
                self.__filters = jira_config["filter"]
            except KeyError:
                pass


    def __load_category_config(self, categories):
        for key in categories:
            category = categories.get(key).split(",")[0].strip()
            self.__categories[key] = category
            colour = categories.get(key).split(",")[1].strip()
            self.__category_colours[category] = colour

        # Add unknown if not configured
        if self.__categories.get("_unknown_") == None:
            self.__categories["_unknown_"] = "Unknown"
            self.__category_colours["Unknown"] = "red"


    @property
    def auth_values(self):
        return self.__auth_values


    @property
    def base_url(self):
        return self.__base_url


    @property
    def category_colours(self):
        return self.__category_colours


    @property
    def first_filter_id(self):
        if len(self.__filters) > 0:
            return list(self.__filters.values())[0]
        return None


    @property
    def teams(self):
        # don't return duplicates
        return list(dict.fromkeys(self.__teams.values()))


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
        return self.__categories.get("_unknown_")

    
    def find_filter_id(self, filter):
        return self.__filters.get(filter)


    def find_status_colour(self, status):
        status_colour = self.__status_colours.get(status)
        if status_colour is None:
            status_colour = "tab:red"

        return status_colour