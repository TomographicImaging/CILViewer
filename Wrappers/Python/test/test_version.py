import unittest


class TestModuleBase(unittest.TestCase):

    def test_version(self):
        try:
            from ccpi.viewer import version as dversion
            a = dversion.version
            print("version", a)
            self.assertTrue(isinstance(a, str))
        except ImportError as ie:
            self.assertFalse(True, str(ie))
