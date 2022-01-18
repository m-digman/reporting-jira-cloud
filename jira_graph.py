import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from enum import Enum, auto


AVERAGE = "Average"
CATEGORY = "Category"
CYCLE_DAYS = "Cycle Days"
LEAD_DAYS = "Lead Days"
RESOLVED = "Resolved"
STATUS = "Status"
STORY_POINTS = "Story Points"
TEAM = "Team"
TICKETS = "Tickets"
TOTAL = "Total"


class jira_graph(object):

    class Columns(Enum):
        CYCLE = auto()
        LEAD = auto()


    def __init__(self, jira_config):
        self.__config = jira_config


    def __plot_monthly_team_ticket_categories(self, team_name, team_data, axis, writer, show_ylabel):
        # Get monthly ticket count for each category 
        team_data = team_data.groupby([pd.Grouper(key=RESOLVED, freq='M'), CATEGORY]).size().to_frame(name=TICKETS).reset_index()
        # Change column to Year-Month (Bug: https://github.com/pandas-dev/pandas/issues/4387)
        team_data[RESOLVED] = team_data[RESOLVED].dt.strftime('%m/%y')
        team_data = team_data.pivot_table(values=TICKETS, index=[RESOLVED], columns=CATEGORY).fillna(0)
        team_data.plot.bar(ax=axis, color=self.__config.category_colours, stacked=True)

        # Total tickets completed for each month
        ticket_total = team_data.sum(axis=1).to_frame(name=TOTAL).reset_index()
        average = ticket_total[TOTAL].mean()
        ticket_total.loc[:, AVERAGE] = average
        ticket_total.plot.line(y=AVERAGE, x=RESOLVED, ax=axis, c="tab:green", lw=2, label="Monthly Avg ({0:.1f})".format(average))

        ylabel = "Tickets Completed" if show_ylabel else ""
        self.__set_labels(axis, team_name, ylabel)
        self.__set_ticket_yticks(axis, True)

        # Add key
        axis.legend(loc='best', fontsize='small', labelspacing=0.2)

        # Add stacked bar values
        for container in axis.containers:
            axis.bar_label(container, fontsize=9, label_type="center")

        team_data.to_excel(writer, sheet_name="{0}_Tickets".format(team_name))
        ticket_total.to_excel(writer, sheet_name="{0}_Total".format(team_name))


    def __set_ticket_yticks(self, axis, start_from_zero):
        next = 0
        yticks = []

        start, end = axis.get_ylim()
        while next <= end:
            if start_from_zero or next > start:
                yticks.append(next)
            if end > 100:
                next += 10
            else:
                next += 5
        
        axis.yaxis.set_ticks(yticks)


    def __plot_monthly_team_ticket_totals(self, team_name, team_data, axis, writer, show_ylabel):
        ticket_data = team_data.groupby([pd.Grouper(key=RESOLVED, freq='M')]).size().to_frame(name=TICKETS).reset_index()
        ticket_data.plot.line(y=TICKETS, x=RESOLVED, ax=axis, c="tab:olive", lw=3, label="Total Tickets")

        avg_tickets = ticket_data[TICKETS].mean()
        ticket_data.loc[:, AVERAGE] = avg_tickets
        ticket_data.plot.line(y=AVERAGE, x=RESOLVED, ax=axis, c="tab:green", lw=2, label="Monthly Avg ({0:.1f})".format(avg_tickets))

        points_data = pd.pivot_table(team_data, values=[STORY_POINTS], index=[pd.Grouper(key=RESOLVED, freq='M')], aggfunc={STORY_POINTS: np.sum}).reset_index()
        points_data.plot.line(y=STORY_POINTS, x=RESOLVED, ax=axis, c="tab:blue", lw=3, label="Total Story Points")

        avg_points = points_data[STORY_POINTS].mean()
        points_data.loc[:, AVERAGE] = avg_points
        points_data.plot.line(y=AVERAGE, x=RESOLVED, ax=axis, c="tab:cyan", lw=2, label="Monthly Avg ({0:.1f})".format(avg_points))

        ylabel = "Number Completed" if show_ylabel else ""
        self.__set_labels(axis, team_name, ylabel)
        self.__set_ticket_yticks(axis, False)

        # Add key
        axis.legend(loc='best', fontsize='small', labelspacing=0.2)

        # Save data as excel tab
        points_data.to_excel(writer, sheet_name="{0}_Points".format(team_name))


    def __set_labels(self, axis, team_name, ylabel_text):
        axis.set_title(team_name, loc="left")
        axis.set_xlabel("")
        axis.set_ylabel(ylabel_text)

        for label in axis.get_xticklabels(which='both'):
            label.set(rotation=45, horizontalalignment='right')


    def __set_yticks(self, axis):
        next = 0
        yticks = []

        start, end = axis.get_ylim()
        while next <= end:
            yticks.append(next)
            if next <= 25 and end <=220:
                next += 5
            else:
                next += 10
        
        axis.yaxis.set_ticks(yticks)


    def __plot_weekly_team_stats(self, team_name, team_data, axis, writer, show_ylabel, column_type):
        legend_label = ""
        if column_type == self.Columns.CYCLE:
            data_column = CYCLE_DAYS
            legend_label = "Cycle Time"
        elif column_type == self.Columns.LEAD:
            data_column = LEAD_DAYS
            legend_label = "Lead Time"

        average = team_data[data_column].mean()
        team_data.loc[:, AVERAGE] = average

        data_avg = pd.pivot_table(team_data, values=[AVERAGE], index=[pd.Grouper(key=RESOLVED, freq='W')]).reset_index()
        data_time = pd.pivot_table(team_data, values=[data_column], index=[pd.Grouper(key=RESOLVED, freq='W')], aggfunc={data_column: np.mean}).reset_index()
        data_min = pd.pivot_table(team_data, values=data_column, index=[pd.Grouper(key=RESOLVED, freq='W')], aggfunc={data_column: min}).reset_index()
        data_max = pd.pivot_table(team_data, values=data_column, index=[pd.Grouper(key=RESOLVED, freq='W')], aggfunc={data_column: max}).reset_index()

        data_avg.plot.line(y=AVERAGE, x=RESOLVED, ax=axis, c="tab:red", lw=2, label="Average ({0:.1f})".format(average))
        data_time.plot.line(y=data_column, x=RESOLVED, ax=axis, c="tab:green", lw=3, label=legend_label)
        data_min.plot.scatter(y=data_column, x=RESOLVED, ax=axis, c="tab:blue", s=35, label="Min")
        data_max.plot.scatter(y=data_column, x=RESOLVED, ax=axis, c="tab:purple", s=35, label="Max")

        ylabel = "Days" if show_ylabel else ""
        self.__set_labels(axis, team_name, ylabel)
        self.__set_yticks(axis)

        # Add key
        axis.legend(loc='upper right', bbox_to_anchor=(1.01, 1.08), ncol=2, fontsize='small', labelspacing=0.2)

        # Save data as excel tab
        team_data.to_excel(writer, sheet_name="{0}_{1}".format(team_name, column_type.name))
        

    def __get_teams_str(self, teams):
        teams_str = ""
        for name in teams:
            teams_str += "_{0}".format(name)
        
        return teams_str


    def __generate_output_filename(self, input_file, teams):
        filename = input_file[0:len(input_file) - 12]
        return filename + self.__get_teams_str(teams)

    
    def __find_matching_teams_to_show(self, requested_teams, teams_in_data):
        teams_to_show = []
        for team_name in requested_teams:
            if team_name in teams_in_data and team_name not in teams_to_show:
                teams_to_show.append(team_name)

        return teams_to_show


    def create_ticket_graphs_by_team(self, input_file, teams):
        if len(input_file) == 0:
            print("Failed to create graph (empty filename)")
        else:
            # Use parse_dates to correctly format column data as datetime
            data = pd.read_csv(input_file, delimiter=',', encoding="UTF-8", parse_dates=[RESOLVED])
        
            # Only report on "Done" issues
            data = data.loc[data[STATUS] == "Done"]
            if len(data) == 0:
                return

            teams_to_show = self.__find_matching_teams_to_show(teams, data[TEAM].unique())
            number_of_teams = len(teams_to_show)

            filename = self.__generate_output_filename(input_file, teams_to_show)
            output_file_xlsx = "{0}.xlsx".format(filename)
            output_file_png = "{0}.png".format(filename)

            # Use a single row for one team, otherwise use columns to represent each team
            graph_rows = 4
            graph_columns = number_of_teams
            if number_of_teams == 1:
                graph_rows = 1
                graph_columns = 4

            fig, axes = plt.subplots(nrows=graph_rows, ncols=graph_columns)

            fig_width = (number_of_teams * 4) + (10 - number_of_teams)
            fig_height = 40
            if number_of_teams == 1:
                fig_width = 30
                fig_height = 12

            fig.set_figwidth(fig_width)
            fig.set_figheight(fig_height)
        
            with pd.ExcelWriter(output_file_xlsx) as writer:
                axis_index = 0

                for team_name in teams_to_show:
                    show_ylabel = axis_index == 0

                    # Filter data for team
                    team_data = data.loc[data[TEAM] == team_name].copy()

                    self.__plot_monthly_team_ticket_categories(team_name, team_data, axes[0] if number_of_teams == 1 else axes[0, axis_index], writer, show_ylabel)
                    self.__plot_monthly_team_ticket_totals(team_name, team_data, axes[1] if number_of_teams == 1 else axes[1, axis_index], writer, show_ylabel)
                    self.__plot_weekly_team_stats(team_name, team_data, axes[2] if number_of_teams == 1 else axes[2,axis_index], writer, show_ylabel, self.Columns.CYCLE)
                    self.__plot_weekly_team_stats(team_name, team_data, axes[3] if number_of_teams == 1 else axes[3,axis_index], writer, show_ylabel, self.Columns.LEAD)

                    axis_index += 1

            # Save graph
            plt.savefig(output_file_png)

            print("Created \"{0}\" and \"{1}\"".format(output_file_xlsx, output_file_png))