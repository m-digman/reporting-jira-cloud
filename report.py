from jira_config import jira_config
from jira_data import jira_data
from jira_graph import jira_graph
import sys

jira_lookup = jira_config()


def extract_csv_data_and_plot(filename, teams):
    plotter = jira_graph(jira_lookup)
    plotter.create_ticket_graphs_by_team(filename, teams)


def get_filter_data_and_plot(filter_id, teams):
    jira_query = jira_data(jira_lookup)
    filename = jira_query.save_filter_data(filter_id)

    extract_csv_data_and_plot(filename, teams)


def get_filter_id(filter_param):
    # Try to lookup as filter name, otherwise assume it's an id
    filter_id = jira_lookup.find_filter_id(filter_param)
    return filter_id if filter_id else filter_param


def parse_teams(configured_teams, teams):
    teams_to_show = []
    for team_name in teams:
        stripped_team_name = team_name.strip()
        if stripped_team_name in configured_teams:
            teams_to_show.append(stripped_team_name)
        else: 
            print("Unknown team: \"{0}\". Options are: {1}".format(team_name, ", ".join(configured_teams)))    

    if len(teams_to_show) == 0:
        print("No teams recognised: {0}, using configured teams".format(teams))
        teams_to_show = configured_teams

    return teams_to_show


def get_default_filter_id():
    filter_id = jira_lookup.first_filter_id
    if filter_id:
        return filter_id
    else:
        print("Error: no filters are configured")


def show_usage():
    print("Usage:\r\n======")
    print("  report.py")
    print("  report.py \"<filter>\"")
    print("  report.py \"<filter>\" \"<teams>\"")
    print("  report.py -t \"<teams>\"")
    print("  report.py -f \"<csv_filename>\"")
    print("  report.py -f \"<csv_filename>\" \"<teams>\"")


def main():
    configured_teams = jira_lookup.teams

    args = sys.argv[1:]
    if len(args) == 0:
        # Try using the first filter configured
        get_filter_data_and_plot(get_default_filter_id(), configured_teams)
    elif len(args) == 1:
        if args[0] == "-h" or args[0] == "-help":
            show_usage()
        else:
            # Assume filter id passed
            get_filter_data_and_plot(get_filter_id(args[0]), configured_teams)
    elif len(args) == 2:
        if args[0] == "-t":
            get_filter_data_and_plot(get_default_filter_id(), parse_teams(configured_teams, args[1].split(",")))
        elif args[0] == "-f":
            extract_csv_data_and_plot(args[1], configured_teams)
        else:
            # Assume filter id and teams passed
            get_filter_data_and_plot(get_filter_id(args[0]), parse_teams(configured_teams, args[1].split(",")))
    elif len(args) == 3:
        if args[0] == "-f":
            extract_csv_data_and_plot(args[1], parse_teams(configured_teams, args[2].split(",")))
        else:
            print("Unknown args: " + str(args))
            show_usage()
    else:
        show_usage()
    

if __name__ == "__main__":
    main()