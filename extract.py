from jira_config import jira_config
from jira_data import jira_data
import sys

jira_lookup = jira_config()


def get_filter_id(filter_param):
    # Try to lookup as filter name, otherwise assume it's an id
    filter_id = jira_lookup.find_filter_id(filter_param)
    return filter_id if filter_id else filter_param


def show_usage():
    print("Usage:\r\n======")
    print("  extract.py")
    print("  extract.py \"<filter>\"")


def main():
    jira_query = jira_data(jira_lookup)

    args = sys.argv[1:]
    if len(args) == 0:
        # Try using the first filter configured
        filter_id = jira_lookup.first_filter_id
        if filter_id:
            jira_query.save_filter_data(filter_id)
        else:
            print("Error: no filters are configured") 
    elif len(args) == 1:
        if args[0] == "-h" or args[0] == "-help":
            show_usage()
        else:
            jira_query.save_filter_data(get_filter_id(args[0]))
    else:
        print("Unknown args: " + str(args))
        show_usage()


if __name__ == "__main__":
    main()