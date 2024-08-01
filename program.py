import os
import re
import pandas as pd
import extract

class CSVColumnExtractor:
    def __init__(self, file_path, column_indices):
        self.file_path = file_path
        self.column_indices = column_indices

    def extract_columns(self):
        # Load the CSV file
        df = pd.read_csv(self.file_path)

        # Extract the specified columns
        columns_data = df.iloc[:, self.column_indices]

        return columns_data
    
    def process_column(self, column_data):
        # Define a mapping for the column values
        value_mapping = {
            'Other': '0',
            'A-P': '1',
            'P-A': '2',
            'F-C(Vertical)': '3',
            'C-F(Vertical)': '4',
            'Lateral(L-R)': '5',
            'Lateral(R-L)': '6',
            'No peristalsis visualized': '7',
            # Add more mappings if needed
        }

        # Replace the values in the column based on the mapping
        processed_column = column_data.replace(value_mapping)

        # Explicitly convert the processed column to integers
        processed_column = processed_column.astype(int)

        return processed_column

def extract_upi_v1r1(filename):
    # Regular expression to extract UPI number and V1R1 number
    match = re.match(r'UPI(\d+)_humanReview\(V(\d+)R(\d+)\)\.csv', filename)
    if match:
        upi_number = match.group(1)
        visit_number = match.group(2)
        record_number = match.group(3)
        return upi_number, visit_number, record_number
    return None, None, None

if __name__ == "__main__":
    # Define the directory containing the CSV files
    directory = '.'  # Use the current directory or specify a different one

    # Define the column indices to extract
    column_indices = [2, 3, 8]  # Column indices for columns 2, 3, and 8 (assuming 0-based indexing)

    # Loop through all CSV files in the directory
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            file_path = os.path.join(directory, filename)
            
            # Extract UPI number and Visit/Record numbers from the filename
            upi_number, visit_number, record_number = extract_upi_v1r1(filename)
            
            if upi_number and visit_number and record_number:
                print(f"Processing file: {filename}")
                print(f"UPI Number: {upi_number}")
                print(f"Visit Number: {visit_number}")
                print(f"Record Number: {record_number}\n")

                # Create an instance of CSVColumnExtractor
                extractor = CSVColumnExtractor(file_path, column_indices)

                # Extract and print the items in the specified columns
                columns_data = extractor.extract_columns()

                # Process the 8th column (index 8 in the CSV, but 2nd in the extracted columns)
                columns_data.iloc[:, 2] = extractor.process_column(columns_data.iloc[:, 2])

                # Filter rows where the difference between values in columns 2 and 3 (indices 2 and 3) is 2
                filtered_data = columns_data[(columns_data.iloc[:, 1] - columns_data.iloc[:, 0]).abs() == 2]

                # Initialize a list to store all indices and their mapped values for this file
                all_mapped_indices = []

                # Collect indices and their mapped values from filtered_data
                for index, row in filtered_data.iterrows():
                    start_value = row.iloc[0]  # Value of the 2nd column
                    end_value = row.iloc[1]    # Value of the 3rd column
                    mapped_value = row.iloc[2] # Mapped value of the 8th column
                    
                    # Collect indices between start_value and end_value (inclusive)
                    all_mapped_indices.append((mapped_value, start_value))

                # Print indices for the current file
                print(f"Indices with mapped values for {filename}: {all_mapped_indices}\n")

                # Call the extraction function from extract.py
                mat_file = f'UPI{upi_number}-Visit{visit_number}-Record{record_number}-Recon.mat'
                dataset_name = 'swSig_1Hz_extracted'
                variable_name = 'swSig_1Hz'

                extract.extract_columns_as_long_row(mat_file, variable_name, all_mapped_indices, dataset_name, verbose=True)
