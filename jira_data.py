from requests.models import HTTPError
from jira_request import jira_request
from datetime import datetime
import csv
import os
import os.path
from pprint import pprint


class jira_data(object):
    # Docs https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-get
    __params_filter = "filter/{0}"
    __params_search = "search?jql={0}&maxResults=100&startAt={1}&fields=summary,status,created,resolutiondate,labels,issuetype,parent,customfield_10014,customfield_10016,customfield_10023,customfield_10024"
    __csv_columns = ["Key","Summary","Category","Team","Status","Created","Resolved","Epic","Epic ID","Issue Type","Story Points","Lead Time","To Do","In Progress","Lead Days","Cycle Days"]


    def __init__(self, jira_config):
        self.__config = jira_config
        self.__jira_api = jira_request(jira_config.base_url, jira_config.auth_values)


    def __create_folder(self, path):
        if not os.path.exists(path):
            os.makedirs(path)


    def __create_csv(self, rows, filter_name):
        path = ".//data//{0}".format(filter_name.replace("/", "_"))
        self.__create_folder(path)

        filename = "{0}//{1:%Y_%m_%d}_tickets.csv".format(path, datetime.now())
        with open(filename, 'w', newline='', encoding="UTF-8") as file:
            writer = csv.writer(file)
            writer.writerow(self.__csv_columns)
            writer.writerows(rows)

        print("Extracted {0} tickets to \"{1}\"".format(len(rows), filename))

        return filename


    def __get_date_from_utc_string(self, date_string):
        if date_string:
            # 2019-03-25T15:26:30.000+0000
            return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%f%z")


    def __calc_date_diff_milliseconds(self, start_date, end_date):
        return int((end_date - start_date).total_seconds() * 1000)


    def __calc_days_from_milliseconds(self, milliseconds):
        return round(milliseconds/(1000*60*60*24), 2)


    def __get_time_in_statuses(self, time_in_status):
        to_do, in_progress = "", ""

        # '3_*:*_1_*:*_256892526_*|*_10000_*:*_1_*:*_258319828_*|*_10001_*:*_1_*:*_0'
        if time_in_status:
            data = time_in_status.split("_*|*_")

            for value in data:
                values = value.split("_*:*_")

                status = self.__jira_api.get_status_name(values[0])
                if status:
                    status = status.lower()
                    if status == "to do":
                        to_do = int(values[2])
                    elif status == "in progress":
                        in_progress = int(values[2])

        return to_do, in_progress


    def __get_team_name(self, key, labels):
        team = self.__config.find_team(labels)
        if (len(team) == 0):
            project = key.split("-")[0].lower()
            team = self.__config.find_team({project})

        if (len(team) == 0):
            print("** Team Not Found [key:{0}, labels:{1}] ".format(key, labels))

        return team


    def __extract_search_results(self, issues, rows):
        for issue in issues:
            jira_key = issue["key"]
            summary = issue["fields"]["summary"]
            status = issue["fields"]["status"]["name"]
            labels = issue["fields"]["labels"]
            issue_type = issue["fields"]["issuetype"]["name"]
            created = self.__get_date_from_utc_string(issue["fields"]["created"])
            resolved = self.__get_date_from_utc_string(issue["fields"]["resolutiondate"])
            time_in_status = issue["fields"]["customfield_10023"]

            epic_id, epic_name = "", ""
            try:
                parent = issue["fields"]["parent"]
                if parent:
                    epic_id = issue["fields"]["parent"]["key"]
                    epic_name = issue["fields"]["parent"]["fields"]["summary"]
            except KeyError:
                pass

            # for team-managed projects, story point estimate is now in custom field 16
            story_points = issue["fields"]["customfield_10016"]
            if not story_points:
                story_points = issue["fields"]["customfield_10024"]

            category = self.__config.find_category(labels)
            team = self.__get_team_name(jira_key, labels)
            to_do, in_progress = self.__get_time_in_statuses(time_in_status)

            resolution_date, lead_time, lead_days, cycle_days = "", "", "", ""
            if resolved:
                resolution_date = resolved.date()
                lead_time = self.__calc_date_diff_milliseconds(created, resolved)
                lead_days = self.__calc_days_from_milliseconds(lead_time)
                if to_do:
                    cycle_days = lead_days - self.__calc_days_from_milliseconds(to_do)

            rows.append([jira_key, summary, category, team, status, created.date(), resolution_date, epic_name,
                         epic_id, issue_type, story_points, lead_time, to_do, in_progress, lead_days, cycle_days])


    def __search_jira(self, jql, start_at):
        url_query = self.__params_search.format(jql, start_at)
        return self.__jira_api.get_api3_request(url_query)


    def __extract_paged_search_data(self, jql, csv_rows):
        start_at = 0
        is_last_page = False

        while not is_last_page:
            data = self.__search_jira(jql, start_at)
            self.__extract_search_results(data["issues"], csv_rows)

            start_index = int(data["startAt"])
            page_size = int(data["maxResults"])
            total_rows = int(data["total"])

            start_at = start_index + page_size
            is_last_page = (start_at >= total_rows)

            # print("{0}, {1}, {2} (next: {3}, last: {4})".format(start_index, page_size, total_rows, start_at, is_last_page))


    def __get_jql_for_filter(self, filter_id):
        data = self.__jira_api.get_api3_request(self.__params_filter.format(filter_id))
        return data["jql"], data["name"]


    def save_filter_data(self, filter_id):
        created_filename = ""
        try:
            jql, filter_name = self.__get_jql_for_filter(filter_id)
            print("Using filter: {0} ({1})".format(filter_name, filter_id))

            csv_rows = []
            self.__extract_paged_search_data(jql, csv_rows)
            created_filename = self.__create_csv(csv_rows, filter_name)
        except HTTPError as err:
            print("Failed to find filter (id: {0}) - {1}".format(filter_id, err))

        return created_filename