from jira_config import jira_config
from jira_request import jira_request
from datetime import datetime
from pprint import pprint
import csv
import sys
from enum import Enum, auto
import os
import os.path


# Docs https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-get
params_filter = "filter/{0}"
params_search = "search?jql={0}&maxResults=999&startAt={1}&fields=summary,status,created,resolutiondate,components,labels,issuetype,customfield_10023,customfield_10024"

jira_lookup = jira_config()


class Filter(Enum):
    SUMMARY = auto()
    DETAIL = auto()


def get_csv_column_names(filter_type):
    col_switcher = {
        Filter.SUMMARY: ["Key", "Summary", "Category", "Team", "Status", "Created", "Resolved"],
        Filter.DETAIL: ["Key", "Summary", "Category", "Team", "Status", "Created", "Resolved", "Issue Type", "Story Points",
                        "Days Open", "To Do", "In Progress", "Ready for Review", "QA Test", "Ready to Release",
                        "QA Test Dev", "Ready for Stage", "QA Test Stage", "Ready for Prod"]
    }
    return col_switcher.get(filter_type, "Invalid filter type")


def create_folder(path):
    if not os.path.exists(path):
        os.mkdir(path)


def create_csv(rows, filter_type, file_name):
    path = ".//data"
    create_folder(path)

    filename = "{0}//{1} ({2:%Y-%m-%d}) {3}.csv".format(path, file_name, datetime.now(), filter_type.name)
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(get_csv_column_names(filter_type))
        writer.writerows(rows)

    print("Extracted {0} tickets to \"{1}\"".format(len(rows), filename))


def get_date_from_utc_string(date):
    if date:
        # 2019-03-25T15:26:30.000+0000
        return datetime.strptime(date.split(".")[0], "%Y-%m-%dT%H:%M:%S").date()


def calc_days(milliseconds):
    return round(int(milliseconds) / (1000*60*60*24), 2)


def get_days_in_status(time_in_status, jira_api):
    to_do, in_progress, ready_for_review, qa_test, ready_to_release = "", "", "", "", ""
    qa_test_dev, ready_for_stage, qa_test_stage, ready_for_prod = "", "", "", ""

    # '3_*:*_1_*:*_256892526_*|*_10000_*:*_1_*:*_258319828_*|*_10001_*:*_1_*:*_0'

    data = time_in_status.split("_*|*_")
    for value in data:
        values = value.split("_*:*_")

        status = jira_api.get_status_name(values[0]).lower()
        # print(status)
        if status == "to do":
            to_do = calc_days(values[2])
        elif status == "in progress":
            in_progress = calc_days(values[2])
        elif status == "ready for review":
            ready_for_review = calc_days(values[2])
        elif status == "qa test":
            qa_test = calc_days(values[2])
        elif status == "ready to release":
            ready_to_release = calc_days(values[2])
        elif status == "qa/test dev":
            qa_test_dev = calc_days(values[2])
        elif status == "ready to promote to stage":
            ready_for_stage = calc_days(values[2])
        elif status == "qa test stage":
            qa_test_stage = calc_days(values[2])
        elif status == "ready to promote to prod":
            ready_for_prod = calc_days(values[2])

    return to_do, in_progress, ready_for_review, qa_test, ready_to_release, qa_test_dev, ready_for_stage, qa_test_stage, ready_for_prod


def extract_search_results(issues, rows, filter_type, jira_api):
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

        created_date = get_date_from_utc_string(created)
        resolution_date = get_date_from_utc_string(resolved)

        category = jira_lookup.find_category(labels)
        team = jira_lookup.find_team(labels)
        if (len(team) == 0):
            print("** Team Not Found [{0}, {1}] ".format(jira_key, labels))

        to_do, in_progress, ready_for_review, qa_test, ready_to_release = "", "", "", "", ""
        qa_test_dev, ready_for_stage, qa_test_stage, ready_for_prod = "", "", "", ""
        if filter_type == Filter.DETAIL and resolved:
            days_open = (resolution_date - created_date).days
            to_do, in_progress, ready_for_review, qa_test, ready_to_release, qa_test_dev, ready_for_stage, qa_test_stage, ready_for_prod = get_days_in_status(time_in_status, jira_api)

        if filter_type == Filter.SUMMARY:
            rows.append([jira_key, summary, category, team, status, created_date, resolution_date])
        elif filter_type == Filter.DETAIL:
            rows.append([jira_key, summary, category, team, status, created_date, resolution_date, issue_type, story_points,
                         days_open, to_do, in_progress, ready_for_review, qa_test, ready_to_release,
                         qa_test_dev, ready_for_stage, qa_test_stage, ready_for_prod])



def search_jira(jql, start_at, jira_api):
    return jira_api.get_api3_request(params_search.format(jql, start_at))


def extract_paged_search_data(jira_api, jql, filter_type, csv_rows):
    start_at = 0
    is_last_page = False

    while not is_last_page:
        data = search_jira(jql, start_at, jira_api)
        extract_search_results(data["issues"], csv_rows, filter_type, jira_api)

        start_index = int(data["startAt"])
        page_size = int(data["maxResults"])
        total_rows = int(data["total"])

        start_at = start_index + page_size
        is_last_page = (start_at >= total_rows)


def get_jql_for_filter(filter_id, jira_api):
    data = jira_api.get_api3_request(params_filter.format(filter_id))
    try:
        description = data["description"].strip()
    except KeyError:
        description = ""

    # Use the Jira filter description as the filename
    # If the filter does not have a description, use the id
    return data["jql"], description if len(description) > 0 else filter_id


def store_search_results(filter_type, filter_id):
    jira_api = jira_request(jira_lookup.base_url, jira_lookup.auth_values)
    jql, file_name = get_jql_for_filter(filter_id, jira_api)

    csv_rows = []
    extract_paged_search_data(jira_api, jql, filter_type, csv_rows)

    create_csv(csv_rows, filter_type, file_name)


def extract_filter_data(filter_param, filter_type):
    # Try to lookup as filter name, otherwise assume it's an id
    filter_id = jira_lookup.find_filter_id(filter_param)
    if filter_id:
        store_search_results(filter_type, filter_id)
    else:
        store_search_results(filter_type, filter_param)


def main():
    args = sys.argv[1:]
    if len(args) == 0:
        # Try using the first filter configured
        filter_id = jira_lookup.get_first_filter_id()
        if filter_id:
            extract_filter_data(filter_id, Filter.SUMMARY)
        else:
            print("Error: no filters are configured") 
    elif len(args) == 1:
        extract_filter_data(args[0], Filter.DETAIL)
    elif len(args) == 2:
        if args[0] == "-d":
            extract_filter_data(args[1], Filter.DETAIL)
        elif args[0] == "-s":
            extract_filter_data(args[1], Filter.SUMMARY)
        else:
            print("Unknown args: " + str(args))
    else:
        print("Unknown args: " + str(args))


if __name__ == "__main__":
    main()