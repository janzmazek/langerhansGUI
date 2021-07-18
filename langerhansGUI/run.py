from langerhans import Data, Analysis, Waves

from langerhansGUI.view import View
from langerhansGUI.controller import Controller


def run():
    data = Data()
    analysis = Analysis()
    waves = Waves()
    view = View()
    Controller(data, analysis, waves, view)
    view.configure()

    view.mainloop()
