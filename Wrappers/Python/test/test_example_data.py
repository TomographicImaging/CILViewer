import unittest
from ccpi.viewer.utils import example_data

class TestExampleData(unittest.TestCase):

    def test_head_data(self):
        data = example_data.HEAD.get()
        expected_dimensions = [64, 64, 93]
        read_dimensions = data.GetDimensions()

        for i in range(0, len(expected_dimensions)):
            self.assertEqual(expected_dimensions[i], read_dimensions[i])


if __name__ == '__main__':
    unittest.main()
