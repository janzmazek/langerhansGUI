from langerhans import Data

from langerhansGUI.view import View
from langerhansGUI.controller import Controller


def run():
    data = Data()
    view = View()
    Controller(data, view)
    view.configure()

    view.mainloop()
