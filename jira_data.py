from jira_request import jira_request
from datetime import datetime
from enum import Enum, auto
import csv
import os
import os.path


class jira_data(object):
    # Docs https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-get
    __params_filter = "filter/{0}"
    __params_search = "search?jql={0}&maxResults=999&startAt={1}&fields=summary,status,created,resolutiondate,components,labels,issuetype,customfield_10023,customfield_10024"


    class Filter(Enum):
        SUMMARY = auto()
        DETAIL = auto()


    def __init__(self, jira_config):
        self.__config = jira_config
        self.__jira_api = jira_request(jira_config.base_url, jira_config.auth_values)



    def __get_csv_column_names(self, filter_type):
        col_switcher = {
            self.Filter.SUMMARY: ["Key", "Summary", "Category", "Team", "Status", "Created", "Resolved"],
            self.Filter.DETAIL: ["Key", "Summary", "Category", "Team", "Status", "Created", "Resolved", "Issue Type", "Story Points",
                            "Days Open", "To Do", "In Progress", "Ready for Review", "QA Test", "Ready to Release",
                            "QA Test Dev", "Ready for Stage", "QA Test Stage", "Ready for Prod"]
        }
        return col_switcher.get(filter_type, "Invalid filter type")


    def __create_folder(self, path):
        if not os.path.exists(path):
            os.mkdir(path)


    def __create_csv(self, rows, filter_type, file_name):
        path = ".//data"
        self.__create_folder(path)

        filename = "{0}//{1} ({2:%Y-%m-%d}) {3}.csv".format(path, file_name, datetime.now(), filter_type.name)
        with open(filename, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(self.__get_csv_column_names(filter_type))
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


    def __extract_search_results(self, issues, rows, filter_type):
        for issue in issues:
            jira_key = issue["key"]
            summary = issue["fields"]["summary"]
            status = issue["fields"]["status"]["name"]
            labels = issue["fields"]["labels"]
            issue_type = issue["fields"]["issuetype"]["name"]
            created = issue["fields"]["created"]
            resolved = issue["fields"]["resolutiondate"]
            time_in_status = issue["fields"]["customfield_10023"]
            story_points = issue["fields"]["customfield_10024"]

            created_date = self.__get_date_from_utc_string(created)
            resolution_date = self.__get_date_from_utc_string(resolved)

            category = self.__config.find_category(labels)
            team = self.__config.find_team(labels)
            if (len(team) == 0):
                print("** Team Not Found [{0}, {1}] ".format(jira_key, labels))

            days_open = ""
            to_do, in_progress, ready_for_review, qa_test, ready_to_release = "", "", "", "", ""
            qa_test_dev, ready_for_stage, qa_test_stage, ready_for_prod = "", "", "", ""
            if filter_type == self.Filter.DETAIL and resolved:
                days_open = (resolution_date - created_date).days
                to_do, in_progress, ready_for_review, qa_test, ready_to_release, qa_test_dev, ready_for_stage, qa_test_stage, ready_for_prod = self.__get_days_in_status(time_in_status)

            if filter_type == self.Filter.SUMMARY:
                rows.append([jira_key, summary, category, team, status, created_date, resolution_date])
            elif filter_type == self.Filter.DETAIL:
                rows.append([jira_key, summary, category, team, status, created_date, resolution_date, issue_type, story_points,
                            days_open, to_do, in_progress, ready_for_review, qa_test, ready_to_release,
                            qa_test_dev, ready_for_stage, qa_test_stage, ready_for_prod])



    def __search_jira(self, jql, start_at):
        return self.__jira_api.get_api3_request(self.__params_search.format(jql, start_at))


    def __extract_paged_search_data(self, jql, filter_type, csv_rows):
        start_at = 0
        is_last_page = False

        while not is_last_page:
            data = self.__search_jira(jql, start_at)
            self.__extract_search_results(data["issues"], csv_rows, filter_type)

            start_index = int(data["startAt"])
            page_size = int(data["maxResults"])
            total_rows = int(data["total"])

            start_at = start_index + page_size
            is_last_page = (start_at >= total_rows)


    def __get_jql_for_filter(self, filter_id):
        data = self.__jira_api.get_api3_request(self.__params_filter.format(filter_id))
        try:
            description = data["description"].strip()
        except KeyError:
            description = ""

        # Use the Jira filter description as the filename
        # If the filter does not have a description, use the id
        return data["jql"], description if len(description) > 0 else filter_id


    def save_filter_data(self, filter_type, filter_id):
        jql, file_name = self.__get_jql_for_filter(filter_id)

        csv_rows = []
        self.__extract_paged_search_data(jql, filter_type, csv_rows)
        return self.__create_csv(csv_rows, filter_type, file_name)