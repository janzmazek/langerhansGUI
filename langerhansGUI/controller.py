import os
import numpy as np
import yaml
import pickle
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import time


class Controller(object):
    """docstring for Controller."""

    def __init__(self, data, view):
        self.data = data
        self.view = view
        self.analysis = False

        self.view.register(self)

        self.current_number = 0
        self.current_stage = 0
        self.busy = False

# ---------------------------- Menu click methods --------------------------- #
    def import_data(self):
        if self.busy:
            return
        filename = self.view.open_file()
        if filename is None:
            return
        try:
            if self.current_stage != 0:
                self.data.reset_computations()
            series = np.loadtxt(filename)
            self.data.import_data(series)
            self.current_stage = "imported"
            self.draw_fig()
        except ValueError as e:
            print(e)

    def import_settings(self):
        if self.current_stage == 0 or self.busy:
            return
        filename = self.view.open_file()
        if filename is None:
            return
        with open(filename, 'r') as stream:
            try:
                settings = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
                raise(ValueError("Could not open settings file."))
        try:
            self.data.import_settings(settings)
            self.data.reset_computations()
            self.current_stage = "imported"
            self.draw_fig()
        except ValueError as e:
            print(e)

    def import_excluded(self):
        if self.current_stage == 0 or self.busy:
            return
        filename = self.view.open_file()
        if filename is None:
            return
        try:
            good_cells = np.loadtxt(filename, dtype=bool)
            self.data.import_good_cells(good_cells)
            self.draw_fig()
        except ValueError as e:
            print(e)

    def import_object(self):
        if self.busy:
            return
        filename = self.view.open_file()
        if filename is None:
            return
        try:
            with open(filename, 'rb') as input:
                self.data = pickle.load(input)
        except Exception as exc:
            print("Unsuccessful: {}.".format(exc))
        self.current_stage = "imported"
        self.draw_fig()

    def edit_settings(self):
        if self.current_stage == 0 or self.busy:
            return
        settings = self.data.get_settings()
        self.view.open_settings_window(settings)

    def save_settings(self):
        if self.data.get_settings() is False:
            return
        filename = self.view.save_as("yaml")
        if filename is None:
            return
        with open(filename, "w") as outfile:
            yaml.dump(self.data.get_settings(), outfile,
                      default_flow_style=False
                      )

    def save_image(self):
        if self.current_stage == 0:
            return
        file = self.view.save_as("pdf")
        if file is None:
            return
        self.__get_fig()
        plt.savefig(file)

    def save_eventplot(self):
        if not self.data.is_analyzed():
            return
        file = self.view.save_as("pdf")
        if file is None:
            return
        fig, ax = plt.subplots()
        checkpoint = 0.05
        for i in self.data.plot_events(ax):
            print(i)
            self.view.update_progressbar(i*100)
            if i > checkpoint:
                checkpoint += 0.05
                self.view.update()
        fig.savefig(file)

    def save_excluded(self):
        if self.current_stage == 0:
            return
        if self.data.get_good_cells() is False:
            return
        filename = self.view.save_as("dat")
        if filename is None:
            return
        np.savetxt(filename, self.data.get_good_cells(), fmt="%i")

    def save_object(self):
        if not self.data.is_analyzed() or self.busy:
            return
        filename = self.view.save_as("pkl")
        if filename is None:
            return
        with open(filename, "wb") as output:
            pickle.dump(self.data, output, pickle.HIGHEST_PROTOCOL)

# --------------------------- Button click methods -------------------------- #

    def filter_click(self):
        if self.current_stage == 0 or self.busy:
            return
        if self.data.get_filtered_slow() is not False or \
                self.data.get_filtered_fast() is not False:
            self.current_stage = "filtered"
            self.draw_fig()
        else:
            try:
                self.busy = True
                checkpoint = 0.1
                for i in self.data.filter():
                    self.view.update_progressbar(i*100)
                    if i > checkpoint:
                        checkpoint += 0.1
                        self.view.update()
                self.busy = False
                self.current_stage = "filtered"
                self.draw_fig()
            except ValueError as e:
                print(e)

    def distributions_click(self):
        if self.current_stage == 0 or self.busy:
            return
        elif self.data.get_distributions() is not False:
            self.current_stage = "distributions"
            self.draw_fig()
        else:
            try:
                self.busy = True
                checkpoint = 0.1
                for i in self.data.compute_distributions():
                    self.view.update_progressbar(i*100)
                    if i > checkpoint:
                        checkpoint += 0.1
                        self.view.update()
                self.busy = False
                self.current_stage = "distributions"
                self.draw_fig()
            except ValueError as e:
                print(e)

    def binarize_click(self):
        if self.current_stage == 0 or self.busy:
            return
        if self.data.get_binarized_slow() is not False or \
                self.data.get_binarized_fast() is not False:
            self.current_stage = "binarized"
            self.draw_fig()
        else:
            try:
                self.busy = True
                checkpoint = 0.1
                for (i, _) in zip(self.data.binarize_fast(),
                                  self.data.binarize_slow()
                                  ):
                    self.view.update_progressbar(i*100)
                    if i > checkpoint:
                        checkpoint += 0.1
                        self.view.update()
                self.busy = False
                self.current_stage = "binarized"
                self.draw_fig()
            except ValueError as e:
                print(e)

    def previous_click(self):
        if self.current_stage == 0:
            return
        if self.current_number > 0:
            self.current_number -= 1
            self.view.cell_number_text.config(text=self.current_number)
            self.draw_fig()

    def next_click(self):
        if self.current_stage == 0:
            return
        if self.current_number < self.data.get_cells()-1:
            self.current_number += 1
            self.view.cell_number_text.config(text=self.current_number)
            self.draw_fig()

    def exclude_click(self):
        if self.current_stage == 0:
            return
        try:
            self.data.exclude(self.current_number)
        except ValueError as e:
            print(e)
        self.draw_fig()

    def unexclude_click(self):
        if self.current_stage == 0:
            return
        try:
            self.data.unexclude(self.current_number)
        except ValueError as e:
            print(e)
        self.draw_fig()

    def autoexclude_click(self):
        if self.current_stage == 0 or self.busy:
            return
        try:
            self.busy = True
            for _ in self.data.autoexclude():
                pass
            self.busy = False
        except ValueError as e:
            print(e)
        self.draw_fig()

    def autolimit_click(self):
        if self.current_stage == 0 or self.busy:
            return
        if self.data.get_activity() is not False:
            return
        try:
            self.busy = True
            checkpoint = 0.02
            for i in self.data.autolimit():
                self.view.update_progressbar(i*100)
                if i > checkpoint:
                    checkpoint += 0.02
                    self.view.update()
            self.busy = False
        except ValueError as e:
            print(e)
        self.draw_fig()

    def __get_fig(self):
        if self.current_stage == "imported":
            fig, (ax1, ax2) = plt.subplots(2, sharex=True)
            self.data.plot(ax1, self.current_number, plots=("mean"))
            ax1.set_xlabel(None)
            self.data.plot(
                ax2, self.current_number, plots=("raw"), protocol=False
                )
            return fig
        elif self.current_stage == "filtered":
            fig, (ax1, ax2) = plt.subplots(2, sharex=True)
            fig.suptitle("Filtered data")
            self.data.plot(ax1, self.current_number, plots=("raw",))
            ax1.set_xlabel(None)
            self.data.plot(
                ax2, self.current_number, plots=("fast",), protocol=False
                )
            return fig
        elif self.current_stage == "distributions":
            fig = plt.figure(constrained_layout=True)
            gs = GridSpec(2, 2, figure=fig)
            ax11 = fig.add_subplot(gs[0, 0])
            ax11.set_title("Distribution of pre-stimulatory signal")
            ax12 = fig.add_subplot(gs[0, 1])
            ax12.set_title("Distribution of post-stimulatory signal")
            ax2 = fig.add_subplot(gs[1, :])
            self.data.plot_distributions(ax11, ax12, self.current_number)
            self.data.plot(
                ax2, self.current_number, plots=("raw", "fast"), noise=True
                )
            ax2.legend()
            return fig
        elif self.current_stage == "binarized":
            fig, (ax1, ax2) = plt.subplots(2, sharex=True)
            fig.suptitle("Binarized data")
            self.data.plot(
                ax1, self.current_number, plots=("raw")
                )
            ax1.set_xlabel(None)
            self.data.plot(
                ax2, self.current_number, plots=("fast", "bin_fast"),
                protocol=False
                )
            return fig

    def draw_fig(self):
        if self.current_stage == 0:
            return
        plt.close()
        self.view.draw_fig(self.__get_fig())

    def apply_parameters_click(self):
        self.data.reset_computations()
        self.current_stage = "imported"
        new_settings = self.__get_values(self.view.entries)
        self.data.import_settings(new_settings)
        self.draw_fig()
        self.view.settings_window.destroy()

    def __get_values(self, parameter):
        if type(parameter) not in (dict, list):
            return float(parameter.get())
        elif type(parameter) is dict:
            dictionary = {}
            for key in parameter:
                dictionary[key] = self.__get_values(parameter[key])
            return dictionary
        elif type(parameter) is list:
            array = []
            for key in parameter:
                array.append(self.__get_values(key))
            return array
