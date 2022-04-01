from jira_config import jira_config
from jira_data import jira_data
from jira_epic import jira_epic
import sys


def filter_data_and_plot(filter_id):
    jira_lookup = jira_config()
    jira_query = jira_data(jira_lookup)
    filename = jira_query.save_filter_data(filter_id)

    epic = jira_epic(jira_lookup)
    epic.get_filter_data_and_plot(filename)


def show_usage():
    print("Usage:\r\n======")
    print("  epics.py \"<filter_id>\"")


def main():
    args = sys.argv[1:]
    if len(args) == 1:
        filter_data_and_plot(args[0])
    else:
        show_usage()


if __name__ == "__main__":
    main()