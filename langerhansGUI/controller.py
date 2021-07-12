import numpy as np
import yaml
import pickle
import matplotlib.pyplot as plt
import seaborn as sns


class Controller(object):
    """docstring for Controller."""

    def __init__(self, data, analysis, view):
        self.data = data
        self.analysis = analysis
        self.view = view

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
            self.view.error(e)

    def import_positions(self):
        if self.busy or self.current_stage == 0:
            return
        filename = self.view.open_file()
        if filename is None:
            return
        try:
            positions = np.loadtxt(filename)
            self.data.import_positions(positions)
        except ValueError as e:
            self.view.error(e)

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
            self.view.error(e)

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
            self.view.error(e)

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
        # if not self.data.is_analyzed() or self.busy:
        if self.busy:
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
        if self.data.get_filtered_fast() is not False:
            self.current_stage = "filtered"
            self.draw_fig()
        else:
            self.busy = True
            try:
                step = 0.1
                checkpoint = step
                for i in self.data.filter_fast():
                    self.view.update_progressbar(i*100)
                    if i > checkpoint:
                        checkpoint += step
                        self.view.update()
                self.current_stage = "filtered"
                self.draw_fig()
            except ValueError as e:
                self.view.error(e)
            self.busy = False

    def distributions_click(self):
        if self.current_stage == 0 or self.busy:
            return
        elif self.data.get_distributions() is not False:
            self.current_stage = "distributions"
            self.draw_fig()
        else:
            self.busy = True
            try:
                step = 0.1
                checkpoint = step
                for i in self.data.compute_distributions():
                    self.view.update_progressbar(i*100)
                    if i > checkpoint:
                        checkpoint += step
                        self.view.update()
                self.current_stage = "distributions"
                self.draw_fig()
            except ValueError as e:
                self.view.error(e)
            self.busy = False

    def binarize_click(self):
        if self.current_stage == 0 or self.busy:
            return
        if self.data.get_binarized_fast() is not False:
            self.current_stage = "binarized"
            self.draw_fig()
        else:
            self.busy = True
            try:
                step = 0.1
                checkpoint = step
                for i in self.data.binarize_fast():
                    self.view.update_progressbar(i*100)
                    if i > checkpoint:
                        checkpoint += step
                        self.view.update()
                self.current_stage = "binarized"
                self.draw_fig()
            except ValueError as e:
                self.view.error(e)
            self.busy = False

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
            self.draw_fig()
        except ValueError as e:
            self.view.error(e)

    def unexclude_click(self):
        if self.current_stage == 0:
            return
        try:
            self.data.unexclude(self.current_number)
            self.draw_fig()
        except ValueError as e:
            self.view.error(e)

    def autoexclude_click(self):
        if self.current_stage == 0 or self.busy:
            return
        self.busy = True
        try:
            for _ in self.data.autoexclude():
                pass
            self.draw_fig()
        except ValueError as e:
            self.view.error(e)
        self.busy = False

    def crop_click(self):
        if self.current_stage == 0 or self.busy:
            return
        self.view.open_crop_window()
        self.current_stage = "binarized"

    def analysis_click(self):
        if self.data.get_positions() is False:
            proceed = self.view.warning(
                "Positions not set. Do you want to proceed?"
                )
            if not proceed:
                return
        try:
            threshold = self.data.get_settings()["Network threshold"]
            self.analysis.import_data(self.data, threshold)
            self.analysis.to_pandas()
        except ValueError as e:
            self.view.error(e)
            return
        self.view.open_analysis_window()

    def waves_click(self):
        if self.data.get_positions() is False:
            self.view.error("Positions not set.")
        proceed = self.view.warning(
            "Calculating wave analysis might take a few minutes. Do you want \
            to proceed?"
        )
        if not proceed:
            return
        try:
            threshold = self.data.get_settings()["Network threshold"]
            self.analysis.import_data(self.data, threshold)

            step = 0.01
            checkpoint = step
            for i in self.analysis.detect_waves():
                self.view.update_progressbar(i*100)
                if i > checkpoint:
                    checkpoint += step
                    self.view.update()
                self.busy = False
        except ValueError as e:
            self.view.error(e)
            return
        self.view.open_waves_window()

    def __get_fig(self):
        if self.current_stage == "imported":
            fig, (ax1, ax2) = plt.subplots(2, sharex=True, tight_layout=True)
            self.data.plot(ax1, self.current_number, plots=("mean"))
            ax1.set_xlabel(None)
            self.data.plot(
                ax2, self.current_number, plots=("raw"), protocol=False
                )
            return fig
        elif self.current_stage == "filtered":
            fig, (ax1, ax2) = plt.subplots(2, sharex=True, tight_layout=True)
            fig.suptitle("Filtered data")
            self.data.plot(ax1, self.current_number, plots=("raw",))
            ax1.set_xlabel(None)
            self.data.plot(
                ax2, self.current_number, plots=("fast",), protocol=False
                )
            return fig
        elif self.current_stage == "distributions":
            fig = plt.figure(tight_layout=True)

            gs = fig.add_gridspec(2, 3,  width_ratios=(1, 8, 1),
                                  wspace=0, hspace=0
                                  )

            ax = fig.add_subplot(gs[0, 1])
            ax_middle = fig.add_subplot(gs[1, 1], sharex=ax)
            ax_left = fig.add_subplot(gs[1, 0], sharey=ax_middle)
            ax_right = fig.add_subplot(gs[1, 2], sharey=ax_middle)

            # plots
            self.data.plot(ax, self.current_number, "raw")
            self.data.plot(ax_middle, self.current_number, ["fast"],
                           protocol=False, noise=True
                           )
            self.data.plot_distributions(ax_left, self.current_number)
            self.data.plot_distributions(ax_right, self.current_number,
                                         "signal"
                                         )

            # no labels
            ax.tick_params(axis="x", labelbottom=False)
            ax_middle.tick_params(axis="y", labelleft=False)
            ax_left.tick_params(axis="x", labelbottom=False)
            ax_right.yaxis.tick_right()
            ax_right.tick_params(axis="y", labelleft=False, labelright=False)
            ax.set_xlabel(None)
            ax_middle.set_ylabel(None)
            ax_left.set_ylabel("Amplitude")
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

    def dynamic_parameters_fig(self):
        dyn_par = ["AD", "AT", "OD", "Ff", "ISI", "ISIV", "TP", "TS"]
        fig, ax = plt.subplots(ncols=4, nrows=2, figsize=(12, 6))
        df = self.analysis.get_dataframe()
        for i in range(2):
            for j in range(4):
                p = dyn_par[i*4+j]
                data = df.loc[df["Par ID"] == p]
                sns.boxplot(ax=ax[i, j], x="Parameter", y="Value", data=data)
                ax[i, j].set_ylabel('')
        return fig

    def glob_network_parameters_fig(self):
        fig, ax = plt.subplots()
        return fig

    def network_parameters_fig(self):
        ind_net_par = ["NDf", "NNDf"]
        fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(12, 6))
        self.analysis.draw_network(ax1)
        df = self.analysis.get_dataframe()
        data = df.loc[df["Par ID"].isin(ind_net_par)]
        sns.boxplot(ax=ax2, x="Parameter", y="Value", data=data)
        ax2.set_ylabel('')
        return fig

    def waves_fig(self):
        fig, ax = plt.subplots()
        self.analysis.plot_events(ax)
        return fig

    def draw_fig(self):
        if self.current_stage == 0:
            return
        plt.close()
        self.view.refresh_canvas(self.__get_fig())

    def apply_parameters_click(self):
        self.data.reset_computations()
        self.current_stage = "imported"
        new_settings = self.__get_values(self.view.entries)
        self.data.import_settings(new_settings)
        self.draw_fig()
        self.view.settings_window.destroy()

    def __get_values(self, parameter, string=False):
        if type(parameter) not in (dict, list):
            if string:
                return parameter.get()
            else:
                return float(parameter.get())
        elif type(parameter) is dict:
            dictionary = {}
            for key in parameter:
                string = True if key in ("Islet ID") else False
                dictionary[key] = self.__get_values(parameter[key], string)
            return dictionary
        elif type(parameter) is list:
            array = []
            for key in parameter:
                array.append(self.__get_values(key))
            return array

    def apply_options_click(self):
        choice_var, start_entry, end_entry = self.view.options
        choice = choice_var.get()
        start, end = float(start_entry.get()), float(end_entry.get())

        self.view.crop_window.destroy()
        if choice == 0:
            self.busy = True
            try:
                checkpoint = 0.02
                for i in self.data.autolimit():
                    self.view.update_progressbar(i*100)
                    if i > checkpoint:
                        checkpoint += 0.02
                        self.view.update()
                self.draw_fig()
            except ValueError as e:
                self.view.error(e)
            self.busy = False
            return

        elif choice == 1:
            self.data.crop(fixed_boundaries=(start, end))

        self.current_stage = "binarized"
        self.draw_fig()
