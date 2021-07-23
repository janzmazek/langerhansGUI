import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from tkinter import ttk
from langerhans import analysis
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import webbrowser


# Window parameters
WIDTH = 1000
HEIGHT = 600

WHITE = "white"
TEXT = "white"
# BG = "#2d2f37"
BG = "#3E4149"

WELCOME_TEXT = "WELCOME\n \
To start analyzing, load a data file (a 2-D matrix readable by np.loadtxt).\n \
Cells should be rows of the matrix, time should be columns of the matrix.\n \
You can save or load current state in the form of a pickle object."

WAVES_TEXT = "..."


class View(tk.Tk):
    """docstring for View."""

    def __init__(self, *args, **kwargs):
        super(View, self).__init__(*args, **kwargs)
        self.title("Analysis of Calcium Signals")

        self.controller = None
        self.window = {"analysis": False, "waves": False}

    def register(self, controller):
        self.controller = controller

    def configure(self):
        menubar = tk.Menu(self)

        importmenu = tk.Menu(menubar, tearoff=0)
        exportmenu = tk.Menu(menubar, tearoff=0)
        editmenu = tk.Menu(menubar, tearoff=0)
        aboutmenu = tk.Menu(menubar, tearoff=0)

        menubar.add_cascade(label="Import", menu=importmenu)
        importmenu.add_command(label="Import data",
                               command=self.controller.import_data
                               )
        importmenu.add_command(label="Import positions",
                               command=self.controller.import_positions
                               )
        importmenu.add_command(label="Import settings",
                               command=self.controller.import_settings
                               )
        importmenu.add_command(label="Import excluded",
                               command=self.controller.import_excluded
                               )
        importmenu.add_command(label="Import object (pickle)",
                               command=self.controller.import_object
                               )
        menubar.add_cascade(label="Export", menu=exportmenu)
        exportmenu.add_command(label="Export settings",
                               command=self.controller.save_settings
                               )
        exportmenu.add_command(label="Export image",
                               command=self.controller.save_image
                               )
        exportmenu.add_command(label="Export event plot",
                               command=self.controller.save_eventplot
                               )
        exportmenu.add_command(label="Export excluded",
                               command=self.controller.save_excluded
                               )
        exportmenu.add_command(label="Export object (pickle)",
                               command=self.controller.save_object
                               )
        menubar.add_cascade(label="Edit", menu=editmenu)
        editmenu.add_command(label="Settings",
                             command=self.controller.edit_settings
                             )
        menubar.add_cascade(label="About", menu=aboutmenu)
        aboutmenu.add_command(label="Info",
                              command=lambda: webbrowser.open(
                                  "https://github.com/janzmazek/cell-networks"
                                  )
                              )

        self.config(menu=menubar)

        # ------------------------------ TOOLBAR ---------------------------- #

        toolbar = tk.LabelFrame(self, text="Preprocessing Tools",
                                padx=5, pady=5, bg=BG, fg=TEXT
                                )
        toolbar.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.NO)

        topframe = tk.Frame(toolbar, bg=BG)
        topframe.pack(anchor="center")

        flt_button = tk.Button(topframe, highlightbackground=BG,
                               text="Filter",
                               command=self.controller.filter_click
                               )
        flt_button.pack(side=tk.LEFT)

        dst_button = tk.Button(topframe, highlightbackground=BG,
                               text="Compute distributions",
                               command=self.controller.distributions_click
                               )
        dst_button.pack(side=tk.LEFT)

        bin_button = tk.Button(topframe, highlightbackground=BG,
                               text="Binarize",
                               command=self.controller.binarize_click
                               )
        bin_button.pack(side=tk.LEFT)

        aex_button = tk.Button(topframe, highlightbackground=BG,
                               text="Autoexclude",
                               command=self.controller.autoexclude_click
                               )
        aex_button.pack(side=tk.LEFT)

        alim_button = tk.Button(topframe, highlightbackground=BG,
                                text="Crop",
                                command=self.controller.crop_click
                                )
        alim_button.pack(side=tk.LEFT)

        waves_button = tk.Button(
            topframe, highlightbackground=BG, text="Wave Analysis",
            command=self.controller.waves_click
        )
        waves_button.pack(side=tk.RIGHT)

        analysis_button = tk.Button(
            topframe, highlightbackground=BG, text="Parameter Analysis",
            command=self.controller.analysis_click
            )
        analysis_button.pack(side=tk.RIGHT, padx=(50, 0))

        # ------------------------------ CANVAS ----------------------------- #

        self.canvas = tk.Canvas(self)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        middleframe = tk.Frame(self.canvas,
                               bg=BG, borderwidth=5, relief=tk.RAISED
                               )
        middleframe.pack(side=tk.TOP, fill="none", expand=True)

        text = tk.Label(middleframe, bg=BG, fg=WHITE, text=WELCOME_TEXT)
        text.pack(anchor="center", padx=10, pady=10)

        data_button = tk.Button(middleframe, highlightbackground=BG,
                                text="Import Data",
                                command=self.controller.import_data
                                )
        data_button.pack(side=tk.LEFT, padx=20, pady=20)

        object_button = tk.Button(middleframe, highlightbackground=BG,
                                  text="Import Object",
                                  command=self.controller.import_object
                                  )
        object_button.pack(side=tk.RIGHT, padx=20, pady=20)

        # ------------------------------ NAVBAR ----------------------------- #

        navbar = tk.LabelFrame(self, text="Navigation",
                               padx=5, pady=5, bg=BG, fg=TEXT
                               )
        navbar.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=tk.NO)

        exclude_button = tk.Button(navbar, highlightbackground=BG,
                                   text="(↓) exclude",
                                   command=self.controller.exclude_click
                                   )
        exclude_button.pack(side=tk.LEFT)

        bottomframe = tk.Frame(navbar, bg=BG)
        bottomframe.pack(side=tk.LEFT, fill="none", expand=True)

        prev_button = tk.Button(bottomframe, highlightbackground=BG,
                                text="(←) Prev",
                                command=self.controller.previous_click
                                )
        prev_button.pack(side=tk.LEFT)

        self.cell_number_text = tk.Label(bottomframe, bg=BG, fg=TEXT, text="0")
        self.cell_number_text.pack(side=tk.LEFT)

        next_button = tk.Button(bottomframe, highlightbackground=BG,
                                text="Next (→)",
                                command=self.controller.next_click
                                )
        next_button.pack(side=tk.LEFT)

        unex_button = tk.Button(navbar, highlightbackground=BG,
                                text="unexclude (↑)",
                                command=self.controller.unexclude_click
                                )
        unex_button.pack(side=tk.RIGHT)

        # --------------------------- PROGRESS BAR -------------------------- #

        self.progressbar = ttk.Progressbar(self, orient=tk.HORIZONTAL,
                                           length=100, mode='determinate'
                                           )
        self.progressbar.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=tk.NO)

        self.bind("<Left>", lambda e: self.controller.previous_click())
        self.bind("<Right>", lambda e: self.controller.next_click())
        self.bind("<Up>", lambda e: self.controller.unexclude_click())
        self.bind("<Down>", lambda e: self.controller.exclude_click())

        self.minsize(width=WIDTH, height=HEIGHT)

        ttk.Style().configure("TNotebook", background="black")
        ttk.Style().map("TNotebook.Tab", background=[("selected", "black")],
                        foreground=[("selected", "black")]
                        )
        ttk.Style().configure("TNotebook.Tab", background="black",
                              foreground="black"
                              )

        self.protocol("WM_DELETE_WINDOW", self.close_main_window)

    def open_file(self):
        filename = filedialog.askopenfilename(
            title="Select file",
            filetypes=(
                ("txt files", "*.txt"),
                ("YAML files", "*.yaml"),
                ("pickle files", "*.pkl")
                )
            )
        if filename == '':
            return None
        return filename

    def open_directory(self):
        """
        This method displays the file dialog box to open file and returns the
        file name.
        """
        directory = filedialog.askdirectory()
        if directory == '':
            return None
        return directory

    def save_as(self, default, extensions):
        filename = filedialog.asksaveasfilename(
            defaultextension=default, filetypes=extensions
            )
        if filename == '':
            return None
        return filename

    def refresh_canvas(self, fig):
        if type(self.canvas) == tk.Canvas:
            self.canvas.destroy()
        else:
            self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def open_settings_window(self, settings):
        # Open window
        self.settings_window = tk.Toplevel()
        self.settings_window.title("Settings")

        # Add upper frame
        main_frame = tk.Frame(self.settings_window, bg=BG)
        main_frame.pack(fill=tk.BOTH, expand=tk.YES)

        self.entries = self.__add_frame(settings, main_frame)

        apply_parameters_button = tk.Button(
            main_frame, highlightbackground=BG, text="Apply parameters",
            command=self.controller.apply_parameters_click
            )
        apply_parameters_button.pack(
            side=tk.BOTTOM, fill=tk.BOTH, expand=tk.YES, padx=5, pady=5
            )

    def __add_frame(self, parameter, container):
        if type(parameter) in (int, float, str):
            e = tk.Entry(container)
            e.pack(side=tk.LEFT)
            e.delete(0, tk.END)
            e.insert(0, parameter)
            return e
        elif type(parameter) is dict:
            dictionary = {}
            for key in parameter:
                parameter_frame = tk.LabelFrame(
                    container, text=key, bg=BG, fg=TEXT
                    )
                parameter_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)
                dictionary[key] = self.__add_frame(
                    parameter[key], parameter_frame
                    )
            return dictionary
        elif type(parameter) is list:
            array = []
            for key in range(len(parameter)):
                array.append(self.__add_frame(parameter[key], container))
            return array

    def open_crop_window(self):
        # Open window
        self.crop_window = tk.Toplevel()
        self.crop_window.title("Crop selection")

        # Add upper frame
        main_frame = tk.Frame(self.crop_window, bg=BG)
        main_frame.pack(fill=tk.BOTH, expand=tk.YES)

        choice_frame = tk.LabelFrame(main_frame, text="Choose strip option",
                                     bg=BG, fg=TEXT
                                     )
        choice_frame.pack(fill=tk.BOTH, expand=tk.YES)

        border_frame = tk.LabelFrame(main_frame, text="Custom border values",
                                     bg=BG, fg=TEXT
                                     )
        border_frame.pack(fill=tk.BOTH, expand=tk.YES)

        choice_var = tk.IntVar()
        text = ("Automatic", "Custom")
        for i in range(2):
            choice = tk.Checkbutton(choice_frame, text=text[i], onvalue=i,
                                    bg=BG, fg=TEXT, variable=choice_var
                                    )
            choice.pack(side=tk.LEFT)

        start_entry = tk.Entry(border_frame)
        start_entry.pack(side=tk.TOP)
        start_entry.delete(0, tk.END)
        start_entry.insert(0, 0)

        end_entry = tk.Entry(border_frame)
        end_entry.pack(side=tk.TOP)
        end_entry.delete(0, tk.END)
        end_entry.insert(0, self.controller.data.get_time()[-1])

        apply_options_button = tk.Button(
            main_frame, highlightbackground=BG, text="Apply parameters",
            command=self.controller.apply_options_click)
        apply_options_button.pack()

        self.options = (choice_var, start_entry, end_entry)

    def draw_fig(self, fig, master):
        canvas = FigureCanvasTkAgg(fig, master=master)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def open_analysis_window(self):
        # Open window
        self.window["analysis"] = tk.Toplevel()
        self.window["analysis"].title("Parameter analysis")
        self.window["analysis"].minsize(width=WIDTH, height=HEIGHT)

        upper_frame = tk.Frame(self.window["analysis"])
        upper_frame.pack(expand=1, fill="both", side=tk.TOP)

        # Status
        status_frame = tk.LabelFrame(upper_frame, text="Tools & Status",
                                     background=BG, foreground=TEXT
                                     )
        status_frame.pack(expand=1, fill="both", side=tk.LEFT)

        status = "Number of all cells: {}\n\
                  Number of good cells: {}\n\
                  Positions set: {}".format(
            self.controller.data.get_cells(),
            self.controller.data.get_good_cells().sum(),
            "False" if self.controller.data.get_positions() is False
            else "True"
        )
        info = tk.Label(status_frame, bg=BG, fg=WHITE, text=status)
        info.pack()

        export_dataframe_button = tk.Button(
            status_frame, text="Export Data", highlightbackground=BG,
            command=self.controller.export_dataframe_click
            )
        export_dataframe_button.pack()

        # Notebook
        notebook_frame = tk.LabelFrame(upper_frame, text="Plots")
        notebook_frame.pack(expand=1, fill="both", side=tk.LEFT)
        nb = ttk.Notebook(notebook_frame)
        self.dynamic_par_tab = ttk.Frame(nb)
        self.network_par_tab = ttk.Frame(nb)

        nb.add(self.dynamic_par_tab, text='Dynamic Parameters')
        nb.add(self.network_par_tab, text='Network Parameters')
        nb.pack(expand=1, fill="both")

        self.analysis_progressbar = ttk.Progressbar(
            self.window["analysis"], orient=tk.HORIZONTAL, length=100,
            mode='determinate'
            )
        self.analysis_progressbar.pack(
            side=tk.BOTTOM, fill=tk.BOTH, expand=tk.NO
            )

        self.window["analysis"].protocol(
            "WM_DELETE_WINDOW", self.close_analysis_window
            )

    def open_waves_window(self):
        # Open window
        self.window["waves"] = tk.Toplevel()
        self.window["waves"].title("Wave analysis")
        self.window["waves"].minsize(width=WIDTH, height=HEIGHT)

        upper_frame = tk.Frame(self.window["waves"])
        upper_frame.pack(expand=1, fill="both", side=tk.TOP)

        # Status
        status_frame = tk.LabelFrame(upper_frame, text="Tools & Status",
                                     background=BG, foreground=TEXT
                                     )
        status_frame.pack(expand=1, fill="both", side=tk.LEFT)

        # Notebook
        notebook_frame = tk.LabelFrame(upper_frame, text="Plots")
        notebook_frame.pack(expand=1, fill="both", side=tk.LEFT)
        nb = ttk.Notebook(notebook_frame)
        self.detection_tab = ttk.Frame(nb)
        self.characterization_tab = ttk.Frame(nb)

        nb.add(self.detection_tab, text="Active Signal")
        nb.add(self.characterization_tab, text="Wave characterization")
        nb.pack(expand=1, fill="both")

        self.waves_progressbar = ttk.Progressbar(self.window["waves"],
                                                 orient=tk.HORIZONTAL,
                                                 length=100, mode='determinate'
                                                 )
        self.waves_progressbar.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=tk.NO)

        self.window["waves"].protocol("WM_DELETE_WINDOW",
                                      self.close_waves_window
                                      )

    def warning(self, message):
        return messagebox.askyesno("Do you want to proceed?", message)

    def error(self, e):
        messagebox.showerror("Error", e)

    def update_progressbar(self, window="main"):
        if window == "main":
            self.progressbar["value"] = self.controller.progress*100
        elif window == "analysis":
            self.analysis_progressbar["value"] = self.controller.progress*100
        elif window == "waves":
            self.waves_progressbar["value"] = self.controller.progress*100

    def close_main_window(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            if self.controller.thread["main"].is_alive():
                self.controller.thread["main"].stop()
                self.controller.thread["main"].join()
            self.destroy()

    def close_analysis_window(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            if self.controller.thread["analysis"].is_alive():
                self.controller.thread["analysis"].stop()
                self.controller.thread["waves"].stop()
                self.controller.thread["analysis"].stop()
                self.controller.thread["analysis"].join()
            self.window["analysis"].destroy()
            self.window["analysis"] = False

    def close_waves_window(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            if self.controller.thread["waves"].is_alive():
                self.controller.thread["waves"].stop()
                self.controller.thread["waves"].join()
            self.window["waves"].destroy()
            self.window["waves"] = False
