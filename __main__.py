from langerhans import Data
from langerhans import Analysis

from src.view import View
from src.controller import Controller

if __name__ == '__main__':
    data = Data()
    view = View()
    controller = Controller(data, view)

    view.mainloop()
