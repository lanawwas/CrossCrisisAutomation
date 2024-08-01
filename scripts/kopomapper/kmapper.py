#!/usr/bin/env python3

import pandas as pd
import os
import argparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the columns we want to compare
COLUMNS_TO_COMPARE = ['name', 'type', 'calculation', 'relevant', 'constraint']

def load_kobo_files(directory: str, verbose: bool):
    survey_data = {}
    files_found = 0
    countries_found = set()
    
    for filename in os.listdir(directory):
        if filename.endswith('.xlsx'):
            country_code = filename[:3].upper()  # Extracting the country code
            file_path = os.path.join(directory, filename)
            try:
                survey_df = pd.read_excel(file_path, sheet_name='survey')
                choices_df = pd.read_excel(file_path, sheet_name='choices')
                survey_data[country_code] = {
                    'survey': survey_df,
                    'choices': choices_df
                }
                files_found += 1
                countries_found.add(country_code)
                if verbose:
                    print(f"Loaded file for country: {country_code}")
            except Exception as e:
                if verbose:
                    print(f"Error loading {filename}: {e}")
    
    if verbose:
        print(f"Number of files found: {files_found}")
        print(f"Number of countries found: {len(countries_found)}")
    
    return survey_data

def load_standard_template(file_path: str, verbose: bool):
    try:
        survey_df = pd.read_excel(file_path, sheet_name='survey')
        choices_df = pd.read_excel(file_path, sheet_name='choices')
        if verbose:
            print("Standard template loaded successfully.")
        return {'survey': survey_df, 'choices': choices_df}
    except Exception as e:
        if verbose:
            print(f"Error loading standard template: {e}")
        return None

def extract_variables(survey_df):
    return survey_df[COLUMNS_TO_COMPARE]

def compare_with_standard(country_data, standard_data, verbose: bool):
    discrepancies = {}
    standard_survey = extract_variables(standard_data['survey'])
    
    if verbose:
        print("Comparing country surveys with standard template...")
    
    for country, data in country_data.items():
        country_survey = extract_variables(data['survey'])
        country_discrepancies = []
        
        if verbose:
            print(f"Processing country: {country}")
        
        # Compare each row in standard survey with country survey
        for _, std_row in standard_survey.iterrows():
            std_name = std_row['name']
            country_row = country_survey[country_survey['name'] == std_name]
            
            if country_row.empty:
                country_discrepancies.append({
                    'name': std_name,
                    'issue': 'Missing in country survey'
                })
            else:
                for col in COLUMNS_TO_COMPARE:
                    if std_row[col] != country_row.iloc[0][col]:
                        country_discrepancies.append({
                            'name': std_name,
                            'column': col,
                            'standard_value': std_row[col],
                            'country_value': country_row.iloc[0][col]
                        })
        
        if country_discrepancies:
            discrepancies[country] = country_discrepancies
            if verbose:
                print(f"Discrepancies found for country: {country}")
        else:
            if verbose:
                print(f"No discrepancies found for country: {country}")
    
    if verbose:
        print(f"Total countries with discrepancies: {len(discrepancies)}")
    
    return discrepancies

def generate_discrepancy_report(discrepancies, output_directory, verbose: bool):
    os.makedirs(output_directory, exist_ok=True)
    master_report = []
    
    if verbose:
        print("Generating discrepancy reports...")
    
    for country, country_discrepancies in discrepancies.items():
        country_df = pd.DataFrame(country_discrepancies)
        country_df['country'] = country
        
        # Save individual country report
        country_report_path = os.path.join(output_directory, f"{country}_discrepancy_report.xlsx")
        country_df.to_excel(country_report_path, index=False)
        if verbose:
            print(f"Generated report for {country}: {country_report_path}")
        
        master_report.append(country_df)
    
    # Combine into master report
    master_df = pd.concat(master_report, ignore_index=True)
    master_report_path = os.path.join(output_directory, "master_discrepancy_report.xlsx")
    master_df.to_excel(master_report_path, index=False)
    
    if verbose:
        print(f"Generated master report: {master_report_path}")
        print("Reports generated successfully.")

def main():
    parser = argparse.ArgumentParser(description="Process KoboToolbox survey files.")
    parser.add_argument("kobo_directory", help="Directory containing KoboToolbox files.")
    parser.add_argument("standard_template_path", help="Path to the standard survey template.")
    parser.add_argument("output_directory", help="Directory to save discrepancy reports.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    
    args = parser.parse_args()
    
    # 1. Input the corresponding Kobo template Ingestion
    country_data = load_kobo_files(args.kobo_directory, args.verbose)
    standard_data = load_standard_template(args.standard_template_path, args.verbose)
    
    if standard_data is None:
        print("Failed to load the standard template. Exiting...")
        return
    
    # 2. Parsing and Initial Mapping
    discrepancies = compare_with_standard(country_data, standard_data, args.verbose)
    
    # 3. Generate Initial Reports
    generate_discrepancy_report(discrepancies, args.output_directory, args.verbose)

if __name__ == "__main__":
    main()
