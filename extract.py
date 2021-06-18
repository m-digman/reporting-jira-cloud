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
params_search = "search?jql={0}&maxResults=999&startAt=0&fields=summary,status,created,resolutiondate,components,labels,issuetype,customfield_10023,customfield_10024"

# Completed work last month
filter_last_month = 10111
# Completed work this month
filter_this_month = 10106


class Filter(Enum):
    SUMMARY = auto()
    DETAIL = auto()


def get_csv_column_names(filter_type):
    col_switcher = {
        Filter.SUMMARY: ["Key", "Summary", "Category", "Team", "Status", "Created", "Resolved"],
        Filter.DETAIL: ["Key", "Summary", "Category", "Team", "Issue Type", "Story Points", "Created", "Resolved",
                        "Days Open", "To Do", "In Progress", "Ready for Review", "QA Test", "Ready to Release"]
    }
    return col_switcher.get(filter_type, "Invalid filter type")


def create_folder(path):
    if not os.path.exists(path):
        os.mkdir(path)


def create_csv(rows, filter_type, file_name):
    path = ".//data"
    create_folder(path)

    # file_name comes from Jira filter description
    filename = "{0}//{1} ({2:%B.%Y}).csv".format(path, file_name, datetime.now())
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(get_csv_column_names(filter_type))
        writer.writerows(rows)

    return filename


def resolve_team_and_category(labels):

    team = ""
    if "SQUAD1" in labels:
        team = "Nova"
    elif "SQUAD2" in labels:
        team = "Compex"
    elif "SQUAD3" in labels:
        team = "Ecom"

    category = "Unknown"
    if "project" in labels:
        category = "Project"
    elif "improvement" in labels:
        category = "Improvement"
    elif "bau" in labels:
        category = "BAU"

    return team, category


def get_date_from_utc_string(date):
    if date:
        # 2019-03-25T15:26:30.000+0000
        return datetime.strptime(date.split(".")[0], "%Y-%m-%dT%H:%M:%S").date()


def calc_days(milliseconds):
    return round(int(milliseconds) / (1000*60*60*24), 2)


def get_time_in_status(time_in_status, jira_api):
    to_do, in_progress, ready_for_review, qa_test, ready_to_release = "", "", "", "", ""

    # '3_*:*_1_*:*_256892526_*|*_10000_*:*_1_*:*_258319828_*|*_10001_*:*_1_*:*_0'

    data = time_in_status.split("_*|*_")
    for value in data:
        values = value.split("_*:*_")

        status = jira_api.get_status_name(values[0]).lower()
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

    return to_do, in_progress, ready_for_review, qa_test, ready_to_release


def extract_search_values(issues, rows, filter_type, jira_api):
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

        team, category = resolve_team_and_category(labels)
        created_date = get_date_from_utc_string(created)
        resolution_date = get_date_from_utc_string(resolved)

        to_do, in_progress, ready_for_review, qa_test, ready_to_release = "", "", "", "", ""
        if filter_type == Filter.DETAIL and resolved:
            days_open = (resolution_date - created_date).days
            to_do, in_progress, ready_for_review, qa_test, ready_to_release = get_time_in_status(time_in_status, jira_api)

        if filter_type == Filter.SUMMARY:
            rows.append([jira_key, summary, category, team, status, created_date, resolution_date])
        elif filter_type == Filter.DETAIL:
            rows.append([jira_key, summary, category, team, issue_type, story_points, created_date, resolution_date,
                         days_open, to_do, in_progress, ready_for_review, qa_test, ready_to_release])



def search_jira(jql, jira_api):
    return jira_api.get_api3_request(params_search.format(jql))


def extract_jql(filter_id, jira_api):
    data = jira_api.get_api3_request(params_filter.format(filter_id))
    return data["jql"], data["description"]


def extract_data(jira_api, filter_type, filter_id):
    jql, file_name = extract_jql(filter_id, jira_api)

    csv_rows = []
    data = search_jira(jql, jira_api)
    #pprint(data)
    extract_search_values(data["issues"], csv_rows, filter_type, jira_api)

    create_csv(csv_rows, filter_type, file_name)


def extract_multiple_data(jira_api, file_name, filter_type, filter_ids):
    csv_rows = []
    for filter_id in filter_ids:
        jql, name = extract_jql(filter_id, jira_api)
        data = search_jira(jql, jira_api)
        extract_search_values(data["issues"], csv_rows, filter_type, jira_api)

    create_csv(csv_rows, filter_type, file_name)


def main():
    jira_api = jira_request()

    args = sys.argv[1:]
    if len(args) == 0:
        extract_data(jira_api, Filter.SUMMARY, filter_this_month)
        extract_data(jira_api, Filter.SUMMARY, filter_last_month)
    elif len(args) == 1:
        if args[0] == "all":
            filter_ids = [filter_this_month, filter_last_month]
            extract_multiple_data(jira_api, "completed-last-60-days", Filter.DETAIL, filter_ids)
        else:
            print("Unknown args: " + str(args))
    else:
        print("Unknown args: " + str(args))


if __name__ == "__main__":
    main()
