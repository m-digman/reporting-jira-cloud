import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

COUNT = "Count"
EPIC = "Epic"
STATUS = "Status"
DONE = "Done"
REJECTED = "Rejected"
TODO = "To Do"


class jira_epic(object):


    def __init__(self, jira_config):
        self.__config = jira_config


    def __get_colours(self, labels):
        colours = []
        for status_label in labels:
            colours.append(self.__config.find_status_colour(status_label))

        return colours


    def __absolute_value(self, val, total):
        return int(np.round(val * total / 100))


    def __plot_data(self, epic_title, epic_data, axis, max_epic_size):
        tickets_in_epic = len(epic_data)
        radius = np.sqrt(tickets_in_epic / max_epic_size)

        status_data = epic_data.groupby([pd.Grouper(key=STATUS)]).size().to_frame(name=COUNT)
        colours = self.__get_colours(status_data.index)

        status_data.plot.pie(y=COUNT, ax=axis, autopct=lambda val: self.__absolute_value(val, tickets_in_epic), colors=colours, radius=radius)
        axis.set_title(epic_title, loc="left")
        axis.set_ylabel("")


    def __clear_unused_subplots(self, num_cols, number_of_epics, last_row_index, axes):
        filled_rows = number_of_epics % num_cols
        if filled_rows > 0:
            for axis_col_index in range(filled_rows, num_cols):
                axes[last_row_index, axis_col_index].remove()


    def __get_max_epic_size(self, data, epics):
        filtered_data = data[data[EPIC].isin(epics)]
        return filtered_data.groupby([pd.Grouper(key=EPIC)]).size().max()


    def __graph_data(self, data, epics, type, output_file):
        output_file_png = "{0}_{1}.png".format(output_file, type)
        title = "{0} [{1}]".format(output_file.split("//")[2], type)

        number_of_epics = len(epics)
        max_epic_size = self.__get_max_epic_size(data, epics)

        num_cols = 5
        if number_of_epics > num_cols:
            num_rows = number_of_epics // num_cols
            if number_of_epics % num_cols > 0:
                num_rows += 1
        else:
            num_cols = number_of_epics
            num_rows = 1

        fig, axes = plt.subplots(ncols=num_cols, nrows=num_rows)
        fig.suptitle(title, fontsize=24)

        fig_width = 9 * num_cols
        fig_height = 8 * num_rows
        fig.set_figwidth(fig_width)
        fig.set_figheight(fig_height)

        epic_index = 0
        axis_col_index = 0

        for epic_name in epics:
            epic_data = data.loc[data[EPIC] == epic_name].copy()
            epic_title = "{0} [{1}]".format(epic_name, epic_data.iloc[0]["Epic ID"])

            if number_of_epics == 1:
                axis = axes
            elif num_rows > 1:
                axis = axes[epic_index // num_cols, axis_col_index]
            else:
                axis = axes[axis_col_index]

            self.__plot_data(epic_title, epic_data, axis, max_epic_size)

            epic_index += 1
            axis_col_index += 1
            if axis_col_index == num_cols:
                axis_col_index = 0

        if num_rows > 1:
            self.__clear_unused_subplots(num_cols, number_of_epics, epic_index // num_cols, axes)

        plt.savefig(output_file_png)

        print("Created \"{0}\"".format(output_file_png))


    def __add_unique_values(self, epics, additional_epics):
        for epic in additional_epics:
            if epic not in epics:
                epics.append(epic)

        return epics


    def __remove_matching_values(self, epics, epics_to_remove):
        for epic in epics_to_remove:
            if epic in epics:
                epics.remove(epic)

        return epics


    def __get_complete_epics(self, data, active_epics):
        # order based on total number of tickets done
        done_data = data[data[STATUS] == DONE].copy()
        done_data = done_data.groupby([EPIC])[STATUS].count().to_frame(name=COUNT).reset_index()
        done_epics = done_data.sort_values([COUNT], ascending=False)[EPIC].unique()

        # add rejected epics
        rejected_epics = data[data[STATUS] == REJECTED][EPIC].unique()
        complete_epics = self.__add_unique_values(list(done_epics), rejected_epics)

        return self.__remove_matching_values(complete_epics, active_epics)


    def __get_active_epics(self, data):
        # order based on the total number of tickets left to do
        todo_data = data[data[STATUS] == TODO].copy()
        todo_data = todo_data.groupby([EPIC])[STATUS].count().to_frame(name=COUNT).reset_index()
        ordered_todo_epics = todo_data.sort_values([COUNT])[EPIC].unique()
    
        # remove epics with only Done and Rejected tickets
        all_active_epics = data[~data[STATUS].isin([DONE, REJECTED])][EPIC].unique()
        active_without_todo = self.__remove_matching_values(list(all_active_epics), ordered_todo_epics)

        return active_without_todo + list(ordered_todo_epics)


    def get_filter_data_and_plot(self, filename):
        data = pd.read_csv(filename, delimiter=',', encoding="UTF-8")
        output_file = filename[0:len(filename) - 4]

        data.loc[data[EPIC].isnull(), EPIC] = "▂▃▅▇█ ┗(°.°)┛ █▇▅▃▂   NO EPIC   ▂▃▅▇█ ┗(°.°)┛ █▇▅▃▂"

        active_epics = self.__get_active_epics(data)
        if len(active_epics) > 0:
            self.__graph_data(data, active_epics, "active", output_file)

        complete_epics = self.__get_complete_epics(data, active_epics)
        if len(complete_epics) > 0:
            self.__graph_data(data, complete_epics, "complete", output_file)