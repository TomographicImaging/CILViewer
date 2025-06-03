import os
import numpy as np

ARRAY_SIZE = (10, 10, 10)
TEST_DATA_FOLDER = os.path.join(os.getcwd(), "Wrappers\\Python\\test\\test_data")

os.makedirs(TEST_DATA_FOLDER, exist_ok=True)

# Generate numpy arrays
random_ints_pos = np.random.randint(low=0, high=256, size=ARRAY_SIZE)
random_ints_neg = np.random.randint(low=-255, high=1, size=ARRAY_SIZE)
random_ints_real = np.random.randint(low=-127, high=128, size=ARRAY_SIZE)
random_floats = np.random.rand(ARRAY_SIZE[0], ARRAY_SIZE[1], ARRAY_SIZE[2])

# Save arrays to NPY files
np.save(os.path.join(TEST_DATA_FOLDER, "random_ints_pos.npy"), random_ints_pos)
np.save(os.path.join(TEST_DATA_FOLDER, "random_ints_neg.npy"), random_ints_neg)
np.save(os.path.join(TEST_DATA_FOLDER, "random_ints_real.npy"), random_ints_real)
np.save(os.path.join(TEST_DATA_FOLDER, "random_floats.npy"), random_floats)

print(f"numpy array test data saved: {TEST_DATA_FOLDER}")
