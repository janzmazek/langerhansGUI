import numpy as np
import yaml
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
import os
import threading

from langerhans import Analysis, Waves


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self,  *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        print("stopped")
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class Controller(object):
    """docstring for Controller."""

    def __init__(self, data, view):
        self.data = data
        self.analysis = False
        self.waves = False
        self.view = view

        self.view.register(self)

        self.current_number = 0
        self.current_stage = 0
        self.thread = {"main": StoppableThread(),
                       "analysis": StoppableThread(),
                       "waves": StoppableThread()
                       }
        self.progress = 0

    def __start_thread(self, next_func=False, window="main",
                       *args, **kwargs):
        self.progress = 0
        self.view.update_progressbar(window)
        self.thread[window] = StoppableThread(*args, **kwargs)
        self.thread[window].start()
        self.view.config(cursor="wait")
        self.__check_completed(next_func, window)

    def __check_completed(self, next_func, window):
        # Check if window has been closed
        if window in ("waves", "analysis"):
            if self.view.window[window] is False:
                self.view.config(cursor="")
                self.progress = 0
                return
        # If window was not closed, check if thread is alive and update
        # progressbar
        if self.thread[window].is_alive():
            self.view.update_progressbar(window)
            self.view.after(
                50, lambda: self.__check_completed(next_func, window)
                )
        else:
            self.view.config(cursor="")
            self.progress = 1
            self.view.update_progressbar(window)
            if window == "main":
                self.draw_fig()
            else:
                next_func()

# ---------------------------- Menu click methods --------------------------- #
    def import_data(self):
        if self.thread["main"].is_alive():
            return
        filename = self.view.open_file()
        if filename is None:
            return
        self.__start_thread(target=self.import_data_thread, args=(filename,))

    def import_data_thread(self, filename):
        try:
            if self.current_stage != 0:
                self.data.reset_computations()
            series = np.loadtxt(filename)
            self.data.import_data(series)
            self.current_stage = "imported"
        except ValueError as e:
            self.view.error(e)

    def import_positions(self):
        if self.thread["main"].is_alive() or self.current_stage == 0:
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
        if self.thread["main"].is_alive() or self.current_stage == 0:
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
        if self.thread["main"].is_alive() or self.current_stage == 0:
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
        if self.thread["main"].is_alive():
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
        if self.thread["main"].is_alive() or self.current_stage == 0:
            return
        settings = self.data.get_settings()
        self.view.open_settings_window(settings)

    def save_settings(self):
        if self.data.get_settings() is False:
            return
        filename = self.view.save_as(".yaml", (("YAML files", "*.yaml"),))
        if filename is None:
            return
        with open(filename, "w") as outfile:
            yaml.dump(self.data.get_settings(), outfile,
                      default_flow_style=False
                      )

    def save_image(self):
        if self.current_stage == 0:
            return
        file = self.view.save_as(".pdf", (("PDF", "*.pdf"),))
        if file is None:
            return
        self.__get_fig()
        plt.savefig(file)

    def save_eventplot(self):
        if not self.data.is_analyzed():
            return
        file = self.view.save_as(".pdf", (("PDF", "*.pdf"),))
        if file is None:
            return
        fig, ax = plt.subplots()
        for _ in self.data.plot_events(ax):
            pass
        fig.savefig(file)

    def save_excluded(self):
        if self.current_stage == 0:
            return
        if self.data.get_good_cells() is False:
            return
        filename = self.view.save_as(".dat", (("RAW text files", "*.dat"),))
        if filename is None:
            return
        np.savetxt(filename, self.data.get_good_cells(), fmt="%i")

    def save_object(self):
        if self.thread["main"].is_alive():
            return
        filename = self.view.save_as(".pkl", (("Pickle files", "*.pkl"),))
        if filename is None:
            return
        with open(filename, "wb") as output:
            pickle.dump(self.data, output, pickle.HIGHEST_PROTOCOL)

# --------------------------- Button click methods -------------------------- #

    def filter_click(self):
        if self.thread["main"].is_alive() or self.current_stage == 0:
            return
        if self.data.get_filtered_fast() is not False:
            self.current_stage = "filtered"
            self.draw_fig()
        else:
            self.__start_thread(target=self.filter_click_thread)

    def filter_click_thread(self):
        try:
            for i in self.data.filter_fast_progress():
                self.progress = i
            self.current_stage = "filtered"
        except ValueError as e:
            self.view.error(e)

    def distributions_click(self):
        if self.thread["main"].is_alive() or self.current_stage == 0:
            return
        elif self.data.get_distributions() is not False:
            self.current_stage = "distributions"
            self.draw_fig()
        else:
            self.__start_thread(target=self.distributions_click_thread)

    def distributions_click_thread(self):
        try:
            for i in self.data.compute_distributions_progress():
                self.progress = i
            self.current_stage = "distributions"
        except ValueError as e:
            self.view.error(e)

    def binarize_click(self):
        if self.thread["main"].is_alive() or self.current_stage == 0:
            return
        if self.data.get_binarized_fast() is not False:
            self.current_stage = "binarized"
            self.draw_fig()
        else:
            self.__start_thread(target=self.binarize_click_thread)

    def binarize_click_thread(self):
        try:
            for i in self.data.binarize_fast_progress():
                self.progress = i
            self.current_stage = "binarized"
        except ValueError as e:
            self.view.error(e)

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
        if self.thread["main"].is_alive() or self.current_stage == 0:
            return
        self.__start_thread(target=self.autoexclude_click_thread)

    def autoexclude_click_thread(self):
        try:
            for i in self.data.autoexclude_progress():
                self.progress = i
        except ValueError as e:
            self.view.error(e)

    def crop_click(self):
        if self.thread["main"].is_alive() or self.current_stage == 0:
            return
        self.view.open_crop_window()
        self.current_stage = "binarized"

    def apply_options_click(self):
        choice_var, start_entry, end_entry = self.view.options
        choice = choice_var.get()
        start, end = float(start_entry.get()), float(end_entry.get())

        self.view.crop_window.destroy()
        if choice == 0:
            self.__start_thread(target=self.autolimit_thread)

        elif choice == 1:
            self.data.crop(fixed_boundaries=(start, end))

    def autolimit_thread(self):
        try:
            for i in self.data.autolimit_progress():
                self.progress = i
                if self.thread["main"].stopped():
                    return
        except ValueError as e:
            self.view.error(e)
        self.current_stage = "binarized"

    def analysis_click(self):
        if self.thread["main"].is_alive():
            self.view.error("Thread busy.")
            return
        if not self.data.is_analyzed():
            self.view.error("Data not analyzed.")
            return
        if self.data.get_positions() is False:
            proceed = self.view.warning(
                "Positions not set. Do you want to proceed?"
                )
            if not proceed:
                return
        self.view.open_analysis_window()
        self.analysis = Analysis()
        try:
            self.__start_thread(target=self.analysis_click_thread,
                                next_func=self.analysis_click_after,
                                window="analysis"
                                )
        except ValueError as e:
            self.view.error(e)

    def analysis_click_thread(self):
        self.view.analysis_labels["status"].set("IN PROGRESS...")
        try:
            self.progress = 0
            threshold = self.data.get_settings()["Network threshold"]
            self.progress = 0.25
            self.analysis.import_data(self.data, threshold)
            self.progress = 0.5
            self.analysis.to_pandas()
        except ValueError as e:
            self.view.error(e)
            return

    def analysis_click_after(self):
        self.view.analysis_labels["status"].set("COMPLETED")
        self.view.draw_fig(self.dynamic_parameters_fig(),
                           self.view.dynamic_par_tab
                           )
        self.view.draw_fig(self.network_parameters_fig(),
                           self.view.network_par_tab
                           )

    def waves_click(self):
        if self.thread["main"].is_alive():
            self.view.error("Thread busy.")
            return
        if not self.data.is_analyzed():
            self.view.error("Data not analyzed.")
            return
        if self.data.get_positions() is False:
            self.view.error("Positions not set.")
            return
        if self.waves is not False:
            return
        self.view.open_waves_window()
        self.waves = Waves()
        try:
            self.waves.import_data(self.data)
            self.__start_thread(target=self.wave_detection,
                                next_func=self.after_wave_detection,
                                window="waves"
                                )
        except ValueError as e:
            self.view.error(e)
            return

    def wave_detection(self):
        try:
            self.view.wave_labels["detection"].set("IN PROGRESS...")
            for i in self.waves.detect_waves():
                self.progress = i
                if self.thread["waves"].stopped():
                    self.view.wave_labels["detection"].set("STOPPED")
                    return
            self.view.wave_labels["detection"].set("COMPLETED")
            self.view.export_act_sig["state"] = "normal"
        except ValueError as e:
            self.view.error(e)

    def after_wave_detection(self):
        if self.thread["waves"].stopped():
            return
        fig, ax = plt.subplots(figsize=(16, 9))
        self.waves.plot_act_sig(ax)
        self.view.draw_fig(fig, self.view.detection_tab)

        self.__start_thread(target=self.wave_characterization,
                            next_func=self.after_wave_characterization,
                            window="waves"
                            )

    def wave_characterization(self):
        try:
            self.view.wave_labels["characterization"].set("IN PROGRESS...")
            for i in self.waves.characterize_waves():
                self.progress = i
                if self.thread["waves"].stopped():
                    self.view.wave_labels["characterization"].set("STOPPED")
                    return
            self.view.wave_labels["characterization"].set("COMPLETED")
        except ValueError as e:
            self.view.error(e)

    def after_wave_characterization(self):
        if self.thread["waves"].stopped():
            return
        fig, ax = plt.subplots(figsize=(16, 9))
        self.waves.plot_events(ax)
        self.view.draw_fig(fig, self.view.characterization_tab)

    def export_dataframe_click(self):
        try:
            dataframe = self.analysis.get_dataframe()
            extensions = (("Excel files", "*.xlsx"), ("CSV files", "*.csv"))
            filename = self.view.save_as(".xlsx", extensions)
            if filename is None:
                return
            _, file_extension = os.path.splitext(filename)
            print(filename, file_extension)
            if file_extension == ".csv":
                dataframe.to_csv(filename)
            elif file_extension == ".xlsx":
                dataframe.to_excel(filename)

        except ValueError as e:
            self.view.error(e)

    def cancel_analysis_click(self):
        self.thread["analysis"].stop()
        self.analysis = False

    def cancel_waves_click(self):
        self.thread["waves"].stop()
        self.waves = False

    def export_act_sig_click(self):
        try:
            act_sig = self.waves.get_act_sig()
            extensions = (("Raw files", "*txt"),)
            filename = self.view.save_as(".txt", extensions)
            if filename is None:
                return
            np.savetxt(filename, act_sig)
        except ValueError as e:
            self.view.error(e)

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
                ax[i, j].set_xlabel('')
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

    def draw_waves_fig(self):
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
