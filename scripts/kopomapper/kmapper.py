#!/usr/bin/env python3

import pandas as pd
import numpy as np
import os
import argparse
import logging
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the columns we want to compare in the survey tab
SURVEY_COLUMNS_TO_COMPARE = ['name', 'type', 'calculation', 'relevant', 'constraint']
# Define the columns we want to compare in the choices tab
CHOICES_COLUMNS_TO_COMPARE = ['name', 'list_name']
# Define the special types
SPECIAL_TYPES = ['begin_group', 'end_group', 'begin_repeat', 'end_repeat']
# Define the label columns for fuzzy matching
LABEL_COLUMNS = ['label::English', 'label::French']

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
                    logging.info(f"Loaded file for country: {country_code}")
            except Exception as e:
                if verbose:
                    logging.error(f"Error loading {filename}: {e}")
    
    if verbose:
        logging.info(f"Number of files found: {files_found}")
        logging.info(f"Number of countries found: {len(countries_found)}")
    
    return survey_data

def load_standard_template(file_path: str, verbose: bool):
    try:
        survey_df = pd.read_excel(file_path, sheet_name='survey')
        choices_df = pd.read_excel(file_path, sheet_name='choices')
        if verbose:
            logging.info("Standard template loaded successfully.")
        return {'survey': survey_df, 'choices': choices_df}
    except Exception as e:
        if verbose:
            logging.error(f"Error loading standard template: {e}")
        return None

def extract_variables(df, columns_to_compare):
    """Extract only the columns that exist in the DataFrame."""
    return df[[col for col in columns_to_compare if col in df.columns]]

def get_available_label_columns(df):
    """Get the label columns that are available in the DataFrame."""
    return [col for col in LABEL_COLUMNS if col in df.columns]

def is_empty_or_nan(value):
    if isinstance(value, float):
        return np.isnan(value)
    return value is None or str(value).strip() == ''

def preprocess_text(text):
    """Preprocess text for better matching."""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = re.sub(r'[_\s]+', ' ', text)  # Replace underscores and multiple spaces with a single space
    return text.strip()

def find_approximate_match(value, candidates, threshold):
    best_match = None
    highest_score = 0
    
    # Convert value to string if it's not already
    value_str = str(value) if value is not None else ""
    
    for candidate in candidates:
        # Convert candidate to string if it's not already
        candidate_str = str(candidate) if candidate is not None else ""
        
        # Skip empty strings
        if not value_str or not candidate_str:
            continue
        
        score = fuzz.token_set_ratio(value_str, candidate_str)
        if score > highest_score and score >= threshold:
            highest_score = score
            best_match = candidate
    return best_match, highest_score

def find_best_match(value, candidates):
    best_match = None
    highest_score = 0
    
    value_str = preprocess_text(value) if not is_empty_or_nan(value) else ""
    
    for candidate in candidates:
        candidate_str = preprocess_text(candidate) if not is_empty_or_nan(candidate) else ""
        
        if not value_str or not candidate_str:
            continue
        
        score = fuzz.partial_ratio(value_str, candidate_str)
        if score > highest_score:
            highest_score = score
            best_match = candidate
    
    return best_match, highest_score

def find_token_match(value, candidates):
    best_match = None
    highest_score = 0
    
    value_str = preprocess_text(value) if not is_empty_or_nan(value) else ""
    
    for candidate in candidates:
        candidate_str = preprocess_text(candidate) if not is_empty_or_nan(candidate) else ""
        
        if not value_str or not candidate_str:
            continue
        
        score = fuzz.token_sort_ratio(value_str, candidate_str)
        if score > highest_score:
            highest_score = score
            best_match = candidate
    
    return best_match, highest_score

def find_label_match(std_value, country_labels, threshold):
    """Find the best label match using multiple techniques."""
    std_value = preprocess_text(std_value)
    country_labels = [preprocess_text(label) for label in country_labels]
    
    # Exact match
    if std_value in country_labels:
        return std_value, 100
    
    # Fuzzy ratio
    best_match, score = process.extractOne(std_value, country_labels, scorer=fuzz.ratio)
    if score >= threshold:
        return best_match, score
    
    # Token sort ratio (handles word order differences)
    best_match, score = process.extractOne(std_value, country_labels, scorer=fuzz.token_sort_ratio)
    if score >= threshold:
        return best_match, score
    
    # Partial ratio (handles substring matches)
    best_match, score = process.extractOne(std_value, country_labels, scorer=fuzz.partial_ratio)
    if score >= threshold:
        return best_match, score
    
    # Token set ratio (handles unordered token matches)
    best_match, score = process.extractOne(std_value, country_labels, scorer=fuzz.token_set_ratio)
    if score >= threshold:
        return best_match, score
    
    # If no match found above threshold, return the best match found
    return best_match, score

def compare_with_standard(country_data, standard_data, verbose: bool, threshold: int):
    discrepancies = {}
    standard_survey = extract_variables(standard_data['survey'], SURVEY_COLUMNS_TO_COMPARE + LABEL_COLUMNS)
    standard_choices = extract_variables(standard_data['choices'], CHOICES_COLUMNS_TO_COMPARE + LABEL_COLUMNS)
    
    standard_survey_label_columns = get_available_label_columns(standard_survey)
    standard_choices_label_columns = get_available_label_columns(standard_choices)
    
    if verbose:
        logging.info("Comparing country surveys with standard template...")
    
    for country, data in country_data.items():
        country_survey = extract_variables(data['survey'], SURVEY_COLUMNS_TO_COMPARE + LABEL_COLUMNS)
        country_choices = extract_variables(data['choices'], CHOICES_COLUMNS_TO_COMPARE + LABEL_COLUMNS)
        
        country_survey_label_columns = get_available_label_columns(country_survey)
        country_choices_label_columns = get_available_label_columns(country_choices)
        
        country_discrepancies = []
        
        if verbose:
            logging.info(f"Processing country: {country}")
        
        # Compare survey tab
        for idx, std_row in standard_survey.iterrows():
            std_name = std_row['name']
            std_type = std_row.get('type', '')  # Use get() to avoid KeyError if 'type' is missing
            if std_type in SPECIAL_TYPES:
                # Skip special types for name matching
                continue
            
            country_row = country_survey[country_survey['name'] == std_name]
            
            if country_row.empty:
                country_discrepancies.append({
                    'tab': 'survey',
                    'row': idx + 2,  # +2 because Excel rows start at 1 and have a header
                    'name': std_name,
                    'issue': 'Missing in country survey',
                    'matched': 'not matched',
                    'approximate_match': None,
                    'best_match': None,
                    'token_match': None,
                    'label_match': None
                })
            else:
                for col in SURVEY_COLUMNS_TO_COMPARE:
                    if col not in std_row or col not in country_row.iloc[0]:
                        continue  # Skip this column if it's not in both standard and country data
                    
                    std_value = std_row[col]
                    country_value = country_row.iloc[0][col]
                    
                    if is_empty_or_nan(std_value) and is_empty_or_nan(country_value):
                        match_status = 'matched'
                        approx_match = None
                        best_match = None
                        token_match = None
                        label_match = None
                    elif std_value != country_value:
                        match_status = 'not matched'
                        approx_match, score = find_approximate_match(std_value, country_survey[col].dropna().unique(), threshold)
                        if score >= threshold:
                            best_match = None
                            token_match = None
                            label_match = None
                        else:
                            best_match, best_score = find_best_match(std_value, country_survey[col].dropna().unique())
                            if best_score >= threshold:
                                token_match = None
                                label_match = None
                            else:
                                token_match, token_score = find_token_match(std_value, country_survey[col].dropna().unique())
                                if token_score < threshold:
                                    if standard_survey_label_columns and country_survey_label_columns:
                                        std_labels = [std_row[label] for label in standard_survey_label_columns if label in std_row.index]
                                        country_labels = country_survey[country_survey_label_columns].stack().dropna().unique()
                                        label_match, label_score = find_label_match(std_labels[0] if std_labels else std_value, country_labels, threshold)
                                    else:
                                        label_match = None
                                else:
                                    label_match = None
                        approx_match = approx_match if score >= threshold else None
                    else:
                        match_status = 'matched'
                        approx_match = None
                        best_match = None
                        token_match = None
                        label_match = None
                    
                    country_discrepancies.append({
                        'tab': 'survey',
                        'row': idx + 2,
                        'name': std_name,
                        'column': col,
                        'standard_value': std_value,
                        'country_value': country_value,
                        'matched': match_status,
                        'approximate_match': approx_match,
                        'best_match': best_match,
                        'token_match': token_match,
                        'label_match': label_match
                    })
        
        # Compare choices tab
        for idx, std_row in standard_choices.iterrows():
            std_name = std_row['name']
            std_list_name = std_row.get('list_name', '')  # Use get() to avoid KeyError if 'list_name' is missing
            country_row = country_choices[(country_choices['name'] == std_name) & 
                                          (country_choices['list_name'] == std_list_name)]
            
            if country_row.empty:
                country_discrepancies.append({
                    'tab': 'choices',
                    'row': idx + 2,
                    'name': std_name,
                    'list_name': std_list_name,
                    'issue': 'Missing in country choices',
                    'matched': 'not matched',
                    'approximate_match': None,
                    'best_match': None,
                    'token_match': None,
                    'label_match': None
                })
            else:
                for col in CHOICES_COLUMNS_TO_COMPARE:
                    if col not in std_row or col not in country_row.iloc[0]:
                        continue  # Skip this column if it's not in both standard and country data
                    
                    std_value = std_row[col]
                    country_value = country_row.iloc[0][col]
                    
                    if is_empty_or_nan(std_value) and is_empty_or_nan(country_value):
                        match_status = 'matched'
                        approx_match = None
                        best_match = None
                        token_match = None
                        label_match = None
                    elif std_value != country_value:
                        match_status = 'not matched'
                        approx_match, score = find_approximate_match(std_value, country_choices[col].dropna().unique(), threshold)
                        if score >= threshold:
                            best_match = None
                            token_match = None
                            label_match = None
                        else:
                            best_match, best_score = find_best_match(std_value, country_choices[col].dropna().unique())
                            if best_score >= threshold:
                                token_match = None
                                label_match = None
                            else:
                                token_match, token_score = find_token_match(std_value, country_choices[col].dropna().unique())
                                if token_score < threshold:
                                    if standard_choices_label_columns and country_choices_label_columns:
                                        std_labels = [std_row[label] for label in standard_choices_label_columns if label in std_row.index]
                                        country_labels = country_choices[country_choices_label_columns].stack().dropna().unique()
                                        label_match, label_score = find_label_match(std_labels[0] if std_labels else std_value, country_labels, threshold)
                                    else:
                                        label_match = None
                                else:
                                    label_match = None
                        approx_match = approx_match if score >= threshold else None
                    else:
                        match_status = 'matched'
                        approx_match = None
                        best_match = None
                        token_match = None
                        label_match = None
                    
                    country_discrepancies.append({
                        'tab': 'choices',
                        'row': idx + 2,
                        'name': std_name,
                        'list_name': std_list_name,
                        'column': col,
                        'standard_value': std_value,
                        'country_value': country_value,
                        'matched': match_status,
                        'approximate_match': approx_match,
                        'best_match': best_match,
                        'token_match': token_match,
                        'label_match': label_match
                    })
        
        if country_discrepancies:
            discrepancies[country] = country_discrepancies
            if verbose:
                logging.info(f"Discrepancies found for country: {country}")
        else:
            if verbose:
                logging.info(f"No discrepancies found for country: {country}")
    
    if verbose:
        logging.info(f"Total countries with discrepancies: {len(discrepancies)}")
    
    return discrepancies

def generate_discrepancy_report(discrepancies, output_directory, verbose: bool):
    os.makedirs(output_directory, exist_ok=True)
    master_report = []
    
    if verbose:
        logging.info("Generating discrepancy reports...")
    
    for country, country_discrepancies in discrepancies.items():
        country_df = pd.DataFrame(country_discrepancies)
        country_df['country'] = country
        
        # Save individual country report
        country_report_path = os.path.join(output_directory, f"{country}_discrepancy_report.xlsx")
        country_df.to_excel(country_report_path, index=False)
        if verbose:
            logging.info(f"Generated report for {country}: {country_report_path}")
        
        master_report.append(country_df)
    
    # Combine into master report
    master_df = pd.concat(master_report, ignore_index=True)
    master_report_path = os.path.join(output_directory, "master_discrepancy_report.xlsx")
    master_df.to_excel(master_report_path, index=False)
    
    if verbose:
        logging.info(f"Generated master report: {master_report_path}")
        logging.info("Reports generated successfully.")

def main():
    parser = argparse.ArgumentParser(description="Process KoboToolbox survey files.")
    parser.add_argument("kobo_directory", help="Directory containing KoboToolbox files.")
    parser.add_argument("standard_template_path", help="Path to the standard survey template.")
    parser.add_argument("output_directory", help="Directory to save discrepancy reports.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    parser.add_argument("--threshold", type=int, default=90, help="Threshold for approximate matching (default: 90).")
    
    args = parser.parse_args()
    
    # 1. Input the corresponding Kobo template Ingestion
    country_data = load_kobo_files(args.kobo_directory, args.verbose)
    standard_data = load_standard_template(args.standard_template_path, args.verbose)
    
    if standard_data is None:
        logging.error("Failed to load the standard template. Exiting...")
        return
    
    # 2. Parsing and Initial Mapping
    discrepancies = compare_with_standard(country_data, standard_data, args.verbose, args.threshold)
    
    # 3. Generate Initial Reports
    generate_discrepancy_report(discrepancies, args.output_directory, args.verbose)

if __name__ == "__main__":
    main()
