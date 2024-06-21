# -*- coding: utf-8 -*-
"""
Created on Thu Jan 11 13:13:44 2024

@author: Ojasvi Mukkoti

This class shows the automation of going through ATP reports, that are CSV files, in a directory.
Will go through all the reports in an indicated folder and create a CSV file thatis formatted in a specfic way.
"""
#THIS IS THE OFFICAL CLASS FOR CONVERTFORMAT
import pandas as pd
import os

#just write this code so that it runs nicely; don't worry about having it work with docker

class ConvertFormat:
    def __init__(self, directory, output_directory):
        """
        Initializes ConvertFormat object with the directory path containing CSV files + the output directory path.

        Args:
            directory (string): Path to the directory containing CSV files
            output_directory (String): path to the directory where the processed CSV files will be saved
        """
        self.directory = directory
        self.output_directory = output_directory
        self.dfs = {} #is a dictionary of dataframes for a year  (Ex: {2019: 'Dataframe of data for 2019', ...})

    def process_file(self, filename):
        """
        Function that processes a single ATP (in CSV format) file 

        Args:
            filename (string): path to the CSV file
        """
        #checking if filename is a csv file
        if filename.endswith(".csv"):
            #creates path to directory of that csv file
            path = os.path.join(self.directory, filename)

            try:
                #reads data from csv file, skipping header rows
                data = pd.read_csv(path, skiprows=6, nrows=34)
            #return these error messages if anything occurs
            except pd.errors.EmptyDataError:
                print(f"EmptyDataError: No data found in file: {filename}")
                return
            except pd.errors.ParserError as e:
                print(f"Error processing file: {filename}, Error{str(e)}")
                return
        
            if os.path.getsize(path) == 0:
                print(f'Warning: {filename} is empty. Skipping...')
                return
            #extracting header information from csv file
            header_df = pd.read_csv(path, header=None, nrows=6)
            category_dict = {}
            for index, row in header_df.iterrows():
                parts = row[0].split(': ')
                category = parts[0]
                value = parts[1] if len(parts) > 1 else None
                category_dict[category] = value
            header_df_final = pd.DataFrame().from_dict(category_dict, orient='index')
            #process the data and create a new Dataframe w/ a specific format like RITAs sheet
            data = pd.read_csv(path, skiprows=6, nrows=34)
            data['Comments'] = data['result'].apply(lambda x: 'NEEDS TO GO TO FINAL INSPECTION' if x == 'PASSED' else 'FAILED')
            #these two categories are the same throughout
            Part_Number = "2AC65A-001"
            Revision = "F"
            #getting specific data from the header to put into dataframe 
            Serial_Number = header_df_final.iloc[3, 0] if len(header_df_final) > 3 else ""
            formatted_serial_num = str(Serial_Number).zfill(7)

            report_Test_Date_str = header_df_final.iloc[1, 0] if len(header_df_final) > 1 else ""
            Test_Operator = header_df_final.iloc[4, 0] if len(header_df_final) > 4 else ""
            Test_Result = header_df_final.iloc[-1, 0] if len(header_df_final) > 0 else ""

            Test_Date = pd.to_datetime(report_Test_Date_str)
            formatted_report_date = Test_Date.strftime('%m/%d/%Y')
            #checking if the Test_Result was PASSED or FAILED
            if Test_Result == 'PASSED':
                Comments = "NEEDS TO GO TO FINAL INSPECTION"
            else:
                Comments = 'FAILED'
            #creating dictionary with the extracted data from the header in ATP report
            data_df = {
                "PART NUMBER": [Part_Number],
                "REVISION": [Revision],
                "SERIAL NUMBER": [formatted_serial_num],
                "BUILD DATE": [""],
                "ASSEMBLER": ['NA'],
                "TEST DATE": [formatted_report_date],
                "REBUILD DATE": ["NA"],
                "TEST OPERATOR": [Test_Operator],
                "TEST RESULT (PASS/FAIL)": [Test_Result],
                "COMMENTS": [Comments],
                "Test Number": [""]
            }
            #creating a Dataframe with the data_df dictionary
            new_df = pd.DataFrame(data_df)

            # Extract year from the report date
            year = Test_Date.year

            # Check if the year is already a key in dfs
            if year not in self.dfs:
                self.dfs[year] = []

            # Append the new_df to the corresponding year key
            self.dfs[year].append(new_df)
            #counting the serial number occurrences
            serial_number_count = {}
            for df_entry in self.dfs[year]:
                for serial_num in df_entry['SERIAL NUMBER']:
                    if serial_num in serial_number_count:
                        serial_number_count[serial_num] +=1
                    else:
                        serial_number_count[serial_num] = 1
            #assigning test numbers to serial numbers
            for df_entry in self.dfs[year]:
                df_entry['Test Number'] = df_entry['SERIAL NUMBER'].map(serial_number_count)

    def process_directory(self):
        """
        Uses the process_file method to process all CSV files in a specified directory
        """
        #going through all the files and folders in a directory
        for root, dirs, files in os.walk(self.directory):
            for filename in files:
                if filename.endswith(".csv"):
                    filepath = os.path.join(root, filename)
                    print(filename)
                    self.process_file(filepath)

    def save_to_csv(self):
        """
        Function saves processed data to a new CSV file.
        """
        #going through 'dfs' dictionary items
        for year, dataframes in self.dfs.items():
            #concating all the dataframes for same year
            result_df = pd.concat(dataframes, ignore_index=True)
            #filename of dataframe for a specifc year
            filename = f"Filename {year}.csv"
            #output path for the new CSV file 
            output_path = os.path.join(self.output_directory, filename)
            #checking if output path exists
            if os.path.exists(output_path):
                #reading the already existing data from output path
                existing_data = pd.read_csv(output_path)
                #concating exisiting data in output directory with new data, drops any duplicates, + resets index
                result_df = pd.concat([existing_data, result_df]).drop_duplicates().reset_index(drop=True)
            #write the result dataframe to csv file
            result_df.to_csv(output_path, index=False)
            ##calling the adding_serial_number method to handle missing serial numbers in the CSV file
            self.adding_serial_number(output_path)

    def adding_serial_number(self, filename):
        """
        Adding missing serial numbers to CSV file.
        """
        try:
            df = pd.read_csv(filename)

            # Convert SERIAL NUMBER column to integer type, skipping invalid values
            df['SERIAL NUMBER'] = pd.to_numeric(df['SERIAL NUMBER'], errors='coerce')

            # Drop rows with NaN values in SERIAL NUMBER column
            df.dropna(subset=['SERIAL NUMBER'], inplace=True)

            # Convert remaining values to integers
            df['SERIAL NUMBER'] = df['SERIAL NUMBER'].astype('Int64')  # Use 'Int64' to handle NaNs as integers

            # Getting the unique serial numbers from the DataFrame
            existing_serial_nums = set(df['SERIAL NUMBER'])

            # Iterate over years and dataframes in self.dfs
            for year, dataframes in self.dfs.items():
                for df_entry in dataframes:
                    new_serial_nums = set(df_entry['SERIAL NUMBER'])

                    missing_serial_nums = new_serial_nums - existing_serial_nums

                    # If missing_serial_nums is not empty, create dataframe for the missing serial numbers
                    if missing_serial_nums:
                        missing_df = pd.DataFrame({'SERIAL NUMBER': list(missing_serial_nums)})
                        df = pd.concat([df, missing_df], ignore_index=True)
            
            print("Values before sorting:", df['SERIAL NUMBER'].unique())
            
            try: 
            # Sort DataFrame by SERIAL NUMBER column
                df.sort_values(by='SERIAL NUMBER', inplace=True)
            except Exception as e_sort:
                print(f"Error sorting file {filename}: {e_sort}. Skipping sorting operation...")

            # Write the DataFrame to CSV file
            df.to_csv(filename, index=False)

        except ValueError as e:
            print(f"Error processing file {filename}: {e}. Skipping this file...")

# Example usage
directory_path = "Directory Path Name"

UNC_ = "{UNC_path_of_Network}"
output_directory = os.path.join(UNC_, "Folder Name that holds ATP reports", 'Subfolder that will dump created file')

converter = ConvertFormat(directory_path, output_directory)
converter.process_directory() 
converter.save_to_csv()
