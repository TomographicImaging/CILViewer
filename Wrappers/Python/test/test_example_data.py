import unittest, os
from ccpi.viewer.utils import example_data

# skip the tests on GitHub actions
if os.environ.get('CONDA_BUILD', '0') == '1':
    skip_test = True
else:
    skip_test = False

print("skip_test is set to ", skip_test)


@unittest.skipIf(skip_test, "Skipping tests on GitHub Actions")
class TestExampleData(unittest.TestCase):

    def test_head_data(self):
        data = example_data.HEAD.get()
        expected_dimensions = [64, 64, 93]
        read_dimensions = data.GetDimensions()

        for i in range(0, len(expected_dimensions)):
            self.assertEqual(expected_dimensions[i], read_dimensions[i])


if __name__ == '__main__':
    unittest.main()
