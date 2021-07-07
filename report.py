from jira_config import jira_config
from jira_data import jira_data
from jira_graph import jira_graph
import sys

jira_lookup = jira_config()


def query_filter_data_and_plot(filter_id, teams):
    jira_query = jira_data(jira_lookup)
    filename = jira_query.save_filter_data(jira_data.Columns.SUMMARY, filter_id)

    plotter = jira_graph(jira_lookup)
    plotter.create_graph(filename, teams)


def extract_csv_data_and_plot(filename, teams):
    plotter = jira_graph(jira_lookup)
    plotter.create_graph(filename, teams)


def get_filter_id(filter_param):
    # Try to lookup as filter name, otherwise assume it's an id
    filter_id = jira_lookup.find_filter_id(filter_param)
    return filter_id if filter_id else filter_param


def parse_valid_teams(configured_teams, teams):
    teams_to_show = []
    for team_name in teams:
        stripped_team_name = team_name.strip()
        if stripped_team_name in configured_teams:
            teams_to_show.append(stripped_team_name)
        else: 
            print("Unknown team: \"{0}\". Options are {1}".format(team_name, configured_teams))    

    return teams_to_show


def show_usage():
    print("Usage:\r\n======")
    print("  report.py \"<filter>\"")
    print("  report.py \"<filter>\" \"<teams>\"")
    print("  report.py -f \"<csv_filename>\"")
    print("  report.py -f \"<csv_filename>\" \"<teams>\"")


def main():
    configured_teams = jira_lookup.teams

    args = sys.argv[1:]
    if len(args) == 0:
        # Try using the first filter configured
        filter_id = jira_lookup.first_filter_id
        if filter_id:
            query_filter_data_and_plot(filter_id, configured_teams)
        else:
            print("Error: no filters are configured") 
    elif len(args) == 1:
        if args[0] == "-h" or args[0] == "-help":
            show_usage()
        else:
            query_filter_data_and_plot(get_filter_id(args[0]), configured_teams)
    elif len(args) == 2:
        if args[0] == "-f":
            extract_csv_data_and_plot(args[1], configured_teams)
        else:
            teams = parse_valid_teams(configured_teams, args[1].split(","))
            if len(teams) > 0:
                query_filter_data_and_plot(get_filter_id(args[0]), teams)
            else:
                print("No teams recognised: {0}".format(args[1]))
    elif len(args) == 3:
        if args[0] == "-f":
            teams = parse_valid_teams(configured_teams, args[2].split(","))
            if len(teams) > 0:
                extract_csv_data_and_plot(args[1], teams)
            else:
                print("No teams recognised: {0}".format(args[2]))
        else:
            print("Unknown args: " + str(args))
            show_usage()
    else:
        show_usage()
    

if __name__ == "__main__":
    main()