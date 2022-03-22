from jira_config import jira_config
from jira_data import jira_data
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys

__status_colours = {"To Do":"silver", "In Progress":"tab:blue", "Ready to Release":"tab:cyan", "Done":"tab:green", "Rejected":"tab:olive"}

COUNT = "Count"
EPIC = "Epic"
STATUS = "Status"


def get_colours(labels):
    colours = []
    for label in labels:
        colours.append(__status_colours.get(label))

    return colours


def absolute_value(val, total):
    return int(np.round(val*total/100))


def plot_data(epic_name, epic_data, axis, max_epic_size):
    tickets_in_epic = len(epic_data)
    radius = np.sqrt(tickets_in_epic / max_epic_size)

    status_data = epic_data.groupby([pd.Grouper(key=STATUS)]).size().to_frame(name=COUNT)
    colours = get_colours(status_data.index)

    status_data.plot.pie(y=COUNT, ax=axis, autopct=lambda val: absolute_value(val, tickets_in_epic), colors=colours, radius=radius)
    axis.set_title(epic_name, loc="left")
    axis.set_ylabel("")


def clear_unused_subplots(num_cols, number_of_epics, last_row_index, axes):
    filled_rows = number_of_epics % num_cols
    if filled_rows > 0:
        # axis index is zero based
        start_col_index = num_cols - filled_rows - 1
        for axis_col_index in range(start_col_index, num_cols):
            axes[last_row_index, axis_col_index].remove()


def graph_data(input_file):
    data = pd.read_csv(input_file, delimiter=',', encoding="UTF-8")
    title = input_file.split("//")[2]

    max_epic_size = data.groupby([pd.Grouper(key=EPIC)]).size().max()

    epics = data[EPIC].unique()
    number_of_epics = len(epics)

    num_cols = 5
    num_rows = number_of_epics // num_cols
    if number_of_epics % num_cols > 0:
        num_rows += 1

    fig, axes = plt.subplots(ncols=num_cols, nrows=num_rows)
    fig.suptitle(title, fontsize=40)


    fig_width = 9 * num_cols
    fig_height = 8 * num_rows
    fig.set_figwidth(fig_width)
    fig.set_figheight(fig_height)

    output_filename = input_file[0:len(input_file) - 4]
    output_file_png = "{0}.png".format(output_filename)

    epic_index = 0
    axis_col_index = 0

    for epic_name in epics:
        epic_data = data.loc[data[EPIC] == epic_name].copy()

        plot_data(epic_name, epic_data, axes[epic_index // num_cols, axis_col_index], max_epic_size)

        epic_index += 1
        axis_col_index += 1
        if axis_col_index == num_cols:
            axis_col_index = 0

    clear_unused_subplots(num_cols, number_of_epics, epic_index // num_cols, axes)

    plt.savefig(output_file_png)

    print("Created \"{0}\"".format(output_file_png))


def get_filter_data_and_plot(filter_id):
    jira_lookup = jira_config()
    jira_query = jira_data(jira_lookup)
    filename = jira_query.save_filter_data(filter_id)

    graph_data(filename)


def show_usage():
    print("Usage:\r\n======")
    print("  epics.py \"<filter_id>\"")


def main():
    args = sys.argv[1:]
    if len(args) == 1:
        get_filter_data_and_plot(args[0])
    else:
        show_usage()


if __name__ == "__main__":
    main()