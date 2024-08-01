import scipy.io
import h5py
import numpy as np
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def matlab_to_python_index(matlab_index):
    """Convert a MATLAB-style index (1-based) to a Python-style index (0-based)."""
    return matlab_index - 1

def extract_upi_visit_and_record(mat_file):
    """Extract visit and record numbers from the MAT file name."""
    match = re.search(r'UPI(\d+)-Visit(\d+)-Record(\d+)', mat_file)
    if match:
        upi, visit, record = match.groups()
        return upi, visit, record
    else:
        raise ValueError("MAT file name does not contain UPI, visit, and record numbers.")

def extract_columns_as_long_row(mat_file, variable_name, mapped_indices, dataset_name, verbose=False):
    try:
        # Load the MAT file
        mat_contents = scipy.io.loadmat(mat_file)

        if verbose:
            # Display the contents to understand its structure
            logging.info("Contents of MAT file:")
            for key, value in mat_contents.items():
                if not key.startswith('__'):
                    logging.info(f"{key}: {type(value)}")
                    if isinstance(value, np.ndarray):
                        logging.info(f"  shape: {value.shape}")

        # Extract from the specified variable
        if variable_name in mat_contents:
            data = mat_contents[variable_name]

            # Check if 'data' is a 2D numpy array
            if isinstance(data, np.ndarray) and data.ndim == 2:
                long_rows = []
                for mapped_value, matlab_index in mapped_indices:
                    # Convert MATLAB index to Python index
                    python_index = matlab_to_python_index(matlab_index)

                    # Ensure indices are within bounds
                    if python_index + 2 < data.shape[1]:
                        # Extract columns for the current index and the next two indices
                        selected_columns = data[:, python_index:python_index + 3]
                        
                        # Concatenate columns into a single long row
                        long_row = np.concatenate([selected_columns[:, i] for i in range(selected_columns.shape[1])])

                        # Prepend the mapped value to the long row
                        long_row = np.insert(long_row, 0, mapped_value)

                        # Append the long row to the list
                        long_rows.append(long_row)

                        if verbose:
                            logging.info(f"Extracted columns based on MATLAB index {matlab_index} as a long row with mapped value {mapped_value}:")
                            logging.info(long_row)
                    else:
                        logging.error(f"Column index {python_index} plus the next two columns exceed the number of columns in the data.")

                if long_rows:
                    # Convert list of long rows to a numpy array
                    long_rows_array = np.array(long_rows)

                    # Construct HDF5 file name
                    upi, visit, record = extract_upi_visit_and_record(mat_file)
                    hdf5_file = f'extracted_columns__UPI{upi}_Visit{visit}_Record{record}.h5'

                    # Save extracted long rows to HDF5 file
                    with h5py.File(hdf5_file, 'w') as f:
                        f.create_dataset(dataset_name, data=long_rows_array)
                        logging.info(f"Extracted long rows saved to {hdf5_file} in dataset '{dataset_name}'")
                else:
                    logging.error("No valid indices found for extraction.")
            else:
                logging.error(f"Variable '{variable_name}' is not a 2D numpy array.")
        else:
            logging.error(f"Variable '{variable_name}' not found in the MAT file.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

def verify_hdf5_contents(hdf5_file, dataset_name):
    try:
        # Open the HDF5 file in read mode
        with h5py.File(hdf5_file, 'r') as f:
            if dataset_name in f:
                data = f[dataset_name][:]
                logging.info(f"Contents of dataset '{dataset_name}' in file '{hdf5_file}':")
                logging.info(data)
            else:
                logging.error(f"Dataset '{dataset_name}' not found in file '{hdf5_file}'")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
