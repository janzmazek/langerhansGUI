import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from tkinter.ttk import Progressbar
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import copy
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


class View(tk.Tk):
    """docstring for View."""

    def __init__(self, *args, **kwargs):
        super(View, self).__init__(*args, **kwargs)
        self.title("Analysis of Calcium Signals")

        self.controller = None

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

        self.toolbar = tk.LabelFrame(self, text="Preprocessing Tools",
                                     padx=5, pady=5, bg=BG, fg=TEXT
                                     )
        self.toolbar.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.NO)

        topframe = tk.Frame(self.toolbar, bg=BG)
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
                                text="Autolimit",
                                command=self.controller.autolimit_click
                                )
        alim_button.pack(side=tk.LEFT)

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

        self.navbar = tk.LabelFrame(self, text="Navigation",
                                    padx=5, pady=5, bg=BG, fg=TEXT
                                    )
        self.navbar.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=tk.NO)

        exclude_button = tk.Button(self.navbar, highlightbackground=BG,
                                   text="(↓) exclude",
                                   command=self.controller.exclude_click
                                   )
        exclude_button.pack(side=tk.LEFT)

        bottomframe = tk.Frame(self.navbar, bg=BG)
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

        unex_button = tk.Button(self.navbar, highlightbackground=BG,
                                text="unexclude (↑)",
                                command=self.controller.unexclude_click
                                )
        unex_button.pack(side=tk.RIGHT)

        self.bind("<Left>", lambda e: self.controller.previous_click())
        self.bind("<Right>", lambda e: self.controller.next_click())
        self.bind("<Up>", lambda e: self.controller.unexclude_click())
        self.bind("<Down>", lambda e: self.controller.exclude_click())

        self.minsize(width=WIDTH, height=HEIGHT)

        self.progressbar = Progressbar(self, orient=tk.HORIZONTAL,
                                       length=100, mode='determinate'
                                       )
        self.progressbar.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=tk.NO)

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

    def save_as(self, extension):
        filename = filedialog.asksaveasfile(
            mode='w', defaultextension=extension
            )
        if filename is None:
            return None
        return filename.name

    def draw_fig(self, fig):
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
        if type(parameter) in (int, float):
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

    def update_progressbar(self, i):
        self.progressbar["value"] = i
