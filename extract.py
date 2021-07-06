from jira_config import jira_config
from jira_data import jira_data
import sys

jira_lookup = jira_config()


def get_filter_id(filter_param):
    # Try to lookup as filter name, otherwise assume it's an id
    filter_id = jira_lookup.find_filter_id(filter_param)
    return filter_id if filter_id else filter_param


def main():
    jira_query = jira_data(jira_lookup)

    args = sys.argv[1:]
    if len(args) == 0:
        # Try using the first filter configured
        filter_id = jira_lookup.get_first_filter_id()
        if filter_id:
            jira_query.save_filter_data(jira_data.Columns.SUMMARY, filter_id)
        else:
            print("Error: no filters are configured") 
    elif len(args) == 1:
        jira_query.save_filter_data(jira_data.Columns.DETAIL, get_filter_id(args[0]))
    elif len(args) == 2:
        if args[0] == "-d":
            jira_query.save_filter_data(jira_data.Columns.DETAIL, get_filter_id(args[1]))
        elif args[0] == "-s":
            jira_query.save_filter_data(jira_data.Columns.SUMMARY, get_filter_id(args[1]))
        else:
            print("Unknown args: " + str(args))
    else:
        print("Unknown args: " + str(args))


if __name__ == "__main__":
    main()