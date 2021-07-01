from jira_config import jira_config
import pandas as pd
import matplotlib.pyplot as plt
import sys


def plot_team_ticket_totals(team_name, data, axis, writer, show_legend, show_ylabel, only_subplot):
    # Filter data for team
    team_data = data.loc[data["Team"] == team_name]
    if len(team_data) == 0:
        return

    # Get monthly ticket count for each category 
    team_data = team_data.groupby([pd.Grouper(key='Resolved', freq='M'), 'Category']).size().to_frame(name='Tickets').reset_index()
    # Change column to Year-Month  (Bug: https://github.com/pandas-dev/pandas/issues/4387)
    team_data['Resolved'] = team_data['Resolved'].dt.strftime('%Y-%m')
    # Pivot data for reporting in graph
    team_data = team_data.pivot_table(values="Tickets", index=["Resolved"], columns="Category").fillna(0)
    # Total tickets completed for each month
    ticket_total = team_data.sum(axis=1).to_frame(name='Total').reset_index()

    # Plot data in graph
    ticket_total.plot.line(y="Total", x="Resolved", ax=axis, color={"Total": "yellowgreen"}, lw=3)
    team_data.plot.bar(ax=axis, color={"Unknown": "firebrick", "Improvement": "royalblue", "BAU": "darkviolet", "Project": "peru"})
    axis.set_xlabel(team_name)
    if show_ylabel:
        axis.set_ylabel("Tickets completed")
    else:
        axis.set_ylabel("")

    if only_subplot:
        axis.legend(loc='upper center', bbox_to_anchor=(0.5, 1.12), ncol=5, fancybox=True, shadow=True)
    elif show_legend:
        axis.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fancybox=True, shadow=True)
    else:
        axis.get_legend().remove()

    # Add bar values and position correctly
    for p in axis.patches:
        axis.annotate(format(p.get_height(), '.0f') if p.get_height() else "", (p.get_x() - 0.04 if p.get_height() > 9 else p.get_x() + 0.01, p.get_height() + 0.3))

    # Save data as excel tab
    team_data.to_excel(writer, sheet_name="{0}_Tickets".format(team_name))
    ticket_total.to_excel(writer, sheet_name="{0}_Total".format(team_name))


def generate_output_filename(input_file, teams):
    filename = ""
    if input_file.endswith("DETAIL.csv"):
        filename = input_file[0:len(input_file) - 10]
    if input_file.endswith("SUMMARY.csv"):
        filename = input_file[0:len(input_file) - 11]
  
    return filename + str(teams).replace(", ", "_")


def load_csv(input_file, teams):
    filename = generate_output_filename(input_file, teams)
    output_file_xlsx = "{0}.xlsx".format(filename)
    output_file_png = "{0}.png".format(filename)

    # Use parse_dates to correctly format column data as datetime
    data = pd.read_csv(input_file, delimiter=',', encoding="ISO-8859-1", parse_dates=['Resolved'])
   
    # Only report on "Done" issues
    data = data.loc[data["Status"] == "Done"]

    # Create separate graphs, 1 for each team
    # Use subplot_kw={'ylim': (0,70)} to set y-axis range
    number_of_teams = len(teams)
    fig, axes = plt.subplots(nrows=1, ncols=number_of_teams)

    only_subplot = number_of_teams == 1

    fig_width = (number_of_teams * 3.5) + (10 - number_of_teams)
    if only_subplot:
        fig_width = 6

    fig.set_figwidth(fig_width)
    fig.set_figheight(5)
   
    with pd.ExcelWriter(output_file_xlsx) as writer:
        axis_index = 0

        for team in teams:
            show_legend = axis_index == number_of_teams - 1
            show_ylabel = axis_index == 0

            plot_team_ticket_totals(team, data, axes if number_of_teams == 1 else axes[axis_index], writer, show_legend, show_ylabel, only_subplot)
            axis_index += 1

    fig.autofmt_xdate(rotation=45)
    #plt.show()

    # Save graph
    plt.savefig(output_file_png)

    print("Created '{0}' and '{1}'".format(output_file_xlsx, output_file_png))


def parse_valid_teams(configured_teams, teams):
    teams_to_show = []
    for team_name in teams:
        stripped_team_name = team_name.strip()
        if stripped_team_name in configured_teams:
            teams_to_show.append(stripped_team_name)
        else: 
            print("Unknown team: \"{0}\". Options are {1}".format(team_name, configured_teams))    

    return teams_to_show


def main():
    jira_lookup = jira_config()
    configured_teams = jira_lookup.get_teams()

    args = sys.argv[1:]
    if len(args) == 1:
        load_csv(args[0], configured_teams)
    elif len(args) == 3:
        if args[1] == "-t":
            # Only display data for teams specified
            teams = parse_valid_teams(configured_teams, args[2].split(","))
            if len(teams) > 0:
                load_csv(args[0], teams)
            else:
                print("No teams recognised: {0}".format(args[2]))
        else:
            print("Unknown args: " + str(args))
            print("Usage: report.py \"<file_name>\" -t \"<team_names>\"")
    else:
        print("Unknown args: " + str(args))
    

if __name__ == "__main__":
    main()