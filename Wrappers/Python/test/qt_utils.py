import unittest
from qtpy.QtWidgets import QApplication


class TestCaseQt(unittest.TestCase):

    @staticmethod
    def get_QApplication(args):
        if QApplication.instance() is None:
            return QApplication(args)
        else:
            return QApplication.instance()
