from jira_config import jira_config
import pandas as pd
import matplotlib.pyplot as plt
import sys


def plot_team_ticket_totals(team_name, data, axis, writer, show_legend):
    # Filter data for team
    team_data = data.loc[data["Team"] == team_name]
    # Get monthly ticket count for each category 
    team_data = team_data.groupby([pd.Grouper(key='Resolved', freq='M'), 'Category']).size().to_frame(name='Tickets').reset_index()
    # Change column to Year-Month  (Bug: https://github.com/pandas-dev/pandas/issues/4387)
    team_data['Resolved'] = team_data['Resolved'].dt.strftime('%Y-%m')
    # Pivot data for reporting in graph
    team_data = team_data.pivot_table(values="Tickets", index=["Resolved"], columns="Category").fillna(0)
    # Total tickets completed for each month
    ticket_total = team_data.sum(axis=1).to_frame(name='Total').reset_index()

    # Plot data in graph
    ticket_total.plot.line(rot=0, y="Total", x="Resolved", color={"Total": "red"}, ax=axis)
    team_data.plot.bar(rot=0, ax=axis)
    axis.set_xlabel(team_name)
    axis.set_ylabel("")
    if show_legend:
        #axis.legend(loc='upper center', bbox_to_anchor=(0.5, 1.12), ncol=5, fancybox=True, shadow=True)
        axis.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fancybox=True, shadow=True, title="")
    else:
        axis.get_legend().remove()

    # Add bar values and position correctly
    for p in axis.patches:
        axis.annotate(format(p.get_height(), '.0f') if p.get_height() else "", (p.get_x() - 0.04 if p.get_height() > 9 else p.get_x() + 0.01, p.get_height() + 0.3))

    # Save data as excel tab
    team_data.to_excel(writer, sheet_name="{0}_Tickets".format(team_name))
    ticket_total.to_excel(writer, sheet_name="{0}_Total".format(team_name))


def load_csv(filename):
    file_csv = "{0}.csv".format(filename)
    file_xlsx = "{0}.xlsx".format(filename)
    file_png = "{0}.png".format(filename)

    # Use parse_dates to correctly format column data as datetime
    data = pd.read_csv(file_csv, delimiter=',', encoding="ISO-8859-1", parse_dates=['Resolved'])
    #print(data)

    jira_lookup = jira_config()
    teams = jira_lookup.get_teams()
    number_of_teams = len(teams)

    # Create separate graphs, 1 for each team
    # Use subplot_kw={'ylim': (0,70)} to set y-axis range
    fig, axes = plt.subplots(nrows=1, ncols=number_of_teams)
    fig.set_figheight(5)
    fig.set_figwidth(number_of_teams*3.5)
   
    with pd.ExcelWriter(file_xlsx) as writer:
        axis_index = 0

        for team in teams:
            plot_team_ticket_totals(team, data, axes[axis_index], writer, axis_index == number_of_teams - 1)
            axis_index += 1

    axes[0].set_ylabel('Tickets completed')
    #plt.show()

    # Save graph
    plt.savefig(file_png)

    print("Created '{0}' and '{1}'".format(file_xlsx, file_png))


def main():
    args = sys.argv[1:]
    if len(args) == 1:
        load_csv(args[0])
    else:
        print("Unknown args: " + str(args))
    

if __name__ == "__main__":
    main()