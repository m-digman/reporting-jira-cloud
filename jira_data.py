from requests.models import HTTPError
from jira_request import jira_request
from datetime import datetime
from enum import Enum, auto
import csv
import os
import os.path
from pprint import pprint


class jira_data(object):
    # Docs https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-get
    __params_filter = "filter/{0}"
    __params_search = "search?jql={0}&maxResults=999&startAt={1}&fields=summary,status,created,resolutiondate,components,labels,issuetype,customfield_10014,customfield_10023,customfield_10024"
    __params_issue = "issue/{0}"
    __epic_name_cache = {}

    class Columns(Enum):
        SUMMARY = auto()
        DETAIL = auto()


    def __init__(self, jira_config):
        self.__config = jira_config
        self.__jira_api = jira_request(jira_config.base_url, jira_config.auth_values)



    def __get_csv_column_names(self, column_type):
        col_switcher = {
            self.Columns.SUMMARY: ["Key", "Summary", "Category", "Team", "Status", "Created", "Resolved"],
            self.Columns.DETAIL: ["Key", "Summary", "Category", "Team", "Status", "Created", "Resolved", "Epic", "Issue Type", "Story Points",
                            "Days Open", "To Do", "In Progress", "Ready for Review", "QA Test", "Ready to Release",
                            "QA Test Dev", "Ready for Stage", "QA Test Stage", "Ready for Prod"]
        }
        return col_switcher.get(column_type, "Invalid column type")


    def __create_folder(self, path):
        if not os.path.exists(path):
            os.makedirs(path)


    def __create_csv(self, rows, column_type, filter_name):
        today = datetime.now()
        path = ".//data//{0}//{1:%Y-%m}".format(filter_name.replace("/", "_"), today)
        self.__create_folder(path)

        filename = "{0}//{1:%d}_{2}.csv".format(path, today, column_type.name)
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.__get_csv_column_names(column_type))
            writer.writerows(rows)

        print("Extracted {0} tickets to \"{1}\"".format(len(rows), filename))

        return filename


    def __get_date_from_utc_string(self, date):
        if date:
            # 2019-03-25T15:26:30.000+0000
            return datetime.strptime(date.split(".")[0], "%Y-%m-%dT%H:%M:%S").date()


    def __calc_days(self, milliseconds):
        return round(int(milliseconds) / (1000*60*60*24), 2)


    def __get_days_in_status(self, time_in_status):
        to_do, in_progress, ready_for_review, qa_test, ready_to_release = "", "", "", "", ""
        qa_test_dev, ready_for_stage, qa_test_stage, ready_for_prod = "", "", "", ""

        # '3_*:*_1_*:*_256892526_*|*_10000_*:*_1_*:*_258319828_*|*_10001_*:*_1_*:*_0'

        data = time_in_status.split("_*|*_")
        for value in data:
            values = value.split("_*:*_")

            status = self.__jira_api.get_status_name(values[0]).lower()
            # print(status)
            if status == "to do":
                to_do = self.__calc_days(values[2])
            elif status == "in progress":
                in_progress = self.__calc_days(values[2])
            elif status == "ready for review":
                ready_for_review = self.__calc_days(values[2])
            elif status == "qa test":
                qa_test = self.__calc_days(values[2])
            elif status == "ready to release":
                ready_to_release = self.__calc_days(values[2])
            elif status == "qa/test dev":
                qa_test_dev = self.__calc_days(values[2])
            elif status == "ready to promote to stage":
                ready_for_stage = self.__calc_days(values[2])
            elif status == "qa test stage":
                qa_test_stage = self.__calc_days(values[2])
            elif status == "ready to promote to prod":
                ready_for_prod = self.__calc_days(values[2])

        return to_do, in_progress, ready_for_review, qa_test, ready_to_release, qa_test_dev, ready_for_stage, qa_test_stage, ready_for_prod


    def __get_team_name(self, key, labels):
        team = self.__config.find_team(labels)
        if (len(team) == 0):
            project = key.split("-")[0].lower()
            team = self.__config.find_team({project})

        if (len(team) == 0):
            print("** Team Not Found [key:{0}, project:{1}, labels:{2}] ".format(key, project, labels))

        return team


    def __extract_search_results(self, issues, rows, column_type):
        for issue in issues:
            jira_key = issue["key"]
            summary = issue["fields"]["summary"]
            status = issue["fields"]["status"]["name"]
            labels = issue["fields"]["labels"]
            issue_type = issue["fields"]["issuetype"]["name"]
            created = issue["fields"]["created"]
            resolved = issue["fields"]["resolutiondate"]
            epic_id = issue["fields"]["customfield_10014"]
            time_in_status = issue["fields"]["customfield_10023"]
            story_points = issue["fields"]["customfield_10024"]

            created_date = self.__get_date_from_utc_string(created)
            resolution_date = self.__get_date_from_utc_string(resolved)

            category = self.__config.find_category(labels)
            team = self.__get_team_name(jira_key, labels)

            days_open = ""
            to_do, in_progress, ready_for_review, qa_test, ready_to_release = "", "", "", "", ""
            qa_test_dev, ready_for_stage, qa_test_stage, ready_for_prod = "", "", "", ""
            if column_type == self.Columns.DETAIL and resolved:
                days_open = (resolution_date - created_date).days
                to_do, in_progress, ready_for_review, qa_test, ready_to_release, qa_test_dev, ready_for_stage, qa_test_stage, ready_for_prod = self.__get_days_in_status(time_in_status)

            if column_type == self.Columns.SUMMARY:
                rows.append([jira_key, summary, category, team, status, created_date, resolution_date])
            elif column_type == self.Columns.DETAIL:
                epic_name = self.__find_epic_name(epic_id)
                rows.append([jira_key, summary, category, team, status, created_date, resolution_date, epic_name, issue_type, story_points,
                            days_open, to_do, in_progress, ready_for_review, qa_test, ready_to_release,
                            qa_test_dev, ready_for_stage, qa_test_stage, ready_for_prod])


    def __retrieve_jira_epic(self, epic_id):
        data = self.__jira_api.get_api3_request(self.__params_issue.format(epic_id))
        return data["fields"]["customfield_10011"]


    def __find_epic_name(self, epic_id):
        epic_name = ""
        if epic_id:
            epic_name = self.__epic_name_cache.get(epic_id)
            if (epic_name == None):
                epic_name = self.__retrieve_jira_epic(epic_id)
                self.__epic_name_cache[epic_id] = epic_name

        return epic_name


    def __search_jira(self, jql, start_at):
        return self.__jira_api.get_api3_request(self.__params_search.format(jql, start_at))


    def __extract_paged_search_data(self, jql, column_type, csv_rows):
        start_at = 0
        is_last_page = False

        while not is_last_page:
            data = self.__search_jira(jql, start_at)
            self.__extract_search_results(data["issues"], csv_rows, column_type)

            start_index = int(data["startAt"])
            page_size = int(data["maxResults"])
            total_rows = int(data["total"])

            start_at = start_index + page_size
            is_last_page = (start_at >= total_rows)


    def __get_jql_for_filter(self, filter_id):
        data = self.__jira_api.get_api3_request(self.__params_filter.format(filter_id))
        return data["jql"], data["name"]


    def save_filter_data(self, column_type, filter_id):
        created_filename = ""
        try:
            jql, filter_name = self.__get_jql_for_filter(filter_id)
            print("Using filter: {0} ({1})".format(filter_name, filter_id))

            csv_rows = []
            self.__extract_paged_search_data(jql, column_type, csv_rows)
            created_filename = self.__create_csv(csv_rows, column_type, filter_name)
        except HTTPError:
            print("Failed to find filter (id: {0})".format(filter_id))

        return created_filename