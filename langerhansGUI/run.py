from langerhans import Data, Analysis

from langerhansGUI.view import View
from langerhansGUI.controller import Controller


def run():
    data = Data()
    analysis = Analysis()
    view = View()
    Controller(data, analysis, view)
    view.configure()

    view.mainloop()
