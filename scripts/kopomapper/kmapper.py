#!/usr/bin/env python3

import pandas as pd
import os
import argparse

# Function to load all KoboToolbox survey files from a directory
def load_kobo_files(directory: str):
    survey_data = {}
    for filename in os.listdir(directory):
        if filename.endswith('.xlsx'):
            country_code = filename[:3]  # Extracting the country code
            file_path = os.path.join(directory, filename)
            try:
                survey_df = pd.read_excel(file_path, sheet_name='survey')
                choices_df = pd.read_excel(file_path, sheet_name='choices')
                survey_data[country_code] = {
                    'survey': survey_df,
                    'choices': choices_df
                }
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    return survey_data

# Function to load the standard survey template
def load_standard_template(file_path: str):
    try:
        survey_df = pd.read_excel(file_path, sheet_name='survey')
        choices_df = pd.read_excel(file_path, sheet_name='choices')
        return {'survey': survey_df, 'choices': choices_df}
    except Exception as e:
        print(f"Error loading standard template: {e}")
        return None

# Function to extract relevant columns from the survey dataframe
def extract_variables(survey_df):
    try:
        return survey_df[['name', 'type', 'calculation', 'relevant', 'constraint']]
    except KeyError:
        print("One or more expected columns are missing in the data.")
        return pd.DataFrame()

# Function to compare country-specific data with the standard template
def compare_with_standard(country_data, standard_data):
    discrepancies = []
    standard_survey = extract_variables(standard_data['survey'])
    
    for country, data in country_data.items():
        country_survey = extract_variables(data['survey'])
        
        # Comparison logic (based on 'name' and 'type' columns, etc.)
        comparison_result = country_survey.compare(standard_survey)
        
        # Log discrepancies
        if not comparison_result.empty:
            discrepancies.append((country, comparison_result))
    
    return discrepancies

# Function to generate reports for each country's discrepancies
def generate_discrepancy_report(discrepancies, output_directory):
    master_report = pd.DataFrame()
    for country, discrepancy in discrepancies:
        # Save individual report
        country_report_path = os.path.join(output_directory, f"{country}_discrepancy_report.xlsx")
        discrepancy.to_excel(country_report_path)
        
        # Combine into master report
        discrepancy['country'] = country
        master_report = pd.concat([master_report, discrepancy])
    
    # Save master report
    master_report_path = os.path.join(output_directory, "master_discrepancy_report.xlsx")
    master_report.to_excel(master_report_path)

# Main function to orchestrate the process
def main():
    # Argument parser
    parser = argparse.ArgumentParser(description="Process KoboToolbox survey files.")
    parser.add_argument("kobo_directory", help="Directory containing KoboToolbox files.")
    parser.add_argument("standard_template_path", help="Path to the standard survey template.")
    parser.add_argument("output_directory", help="Directory to save discrepancy reports.")
    
    args = parser.parse_args()
    
    # Load data
    country_data = load_kobo_files(args.kobo_directory)
    standard_data = load_standard_template(args.standard_template_path)
    
    # Check if the standard data was loaded successfully
    if standard_data is None:
        print("Failed to load the standard template. Exiting...")
        return
    
    # Compare and flag discrepancies
    discrepancies = compare_with_standard(country_data, standard_data)
    
    # Generate reports
    generate_discrepancy_report(discrepancies, args.output_directory)

if __name__ == "__main__":
    main()
