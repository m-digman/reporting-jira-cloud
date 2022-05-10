from jira_config import jira_config
from jira_data import jira_data
from jira_epic import jira_epic
import sys

jira_lookup = jira_config()


def get_filter_id(filter_param):
    # Try to lookup as filter name, otherwise assume it's an id
    filter_id = jira_lookup.find_filter_id(filter_param)
    return filter_id if filter_id else filter_param


def filter_data_and_plot(filter_id):
    jira_query = jira_data(jira_lookup)
    filename = jira_query.save_filter_data(filter_id)

    if filename:
        epic = jira_epic(jira_lookup)
        epic.get_filter_data_and_plot(filename)


def show_usage():
    print("Usage:\r\n======")
    print("  epics.py \"<filter>\"")


def main():
    args = sys.argv[1:]
    if len(args) == 1:
        filter_id = get_filter_id(args[0])
        filter_data_and_plot(filter_id)
    else:
        show_usage()


if __name__ == "__main__":
    main()