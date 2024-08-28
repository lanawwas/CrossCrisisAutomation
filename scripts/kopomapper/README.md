Special Case Handling for type:

    The script now skips rows where the type is one of the special types (begin_group, end_group, begin_repeat, end_repeat) during the name matching process. This prevents incorrect matches due to multiple occurrences of these types.

Independent Column Comparison:

    Each column defined in SURVEY_COLUMNS_TO_COMPARE and CHOICES_COLUMNS_TO_COMPARE is compared independently. Discrepancies are logged for each column separately.

## How It Works:

    Loading Files:
        The script loads the KoboToolbox survey files for each country and the standard template.
    Extracting Variables:
        The script extracts the relevant columns from both the country files and the standard template.
    Comparing Data:
        For the 'survey' tab, it compares each row in the standard template with the corresponding row in the country file based on the 'name' column, except for rows with special types.
        For the 'choices' tab, it performs a similar comparison based on the 'name' and 'list_name' columns.
    Generating Reports:
        The script generates individual discrepancy reports for each country and a master report combining all discrepancies.
## Installation

- Clone the repo. 
- create a python virtual enviroment in the directory of the script 

    ```bash
    python -m venv <nameOfTheVirtualEnviroment> 
    ```

- activate the created virtual enviroment 

    ```bash
    source /path/to/the/created/virtual/enviroment/bin/activate 
    ```
- OR in case of Windows

    ```bash
    source /path/to/the/created/virtual/enviroment/Scripts/activate 

- Install requirments.txt in the virtual enviroment 

    ```bash
    pip install -r requirment.txt
    ```

### Set Execute Permission:
To make the script executable, you need to set the execute permission. You can do this using the chmod command in the terminal:

```bash
chmod +x kmapper.py
```
## Running the Script

You can now run the script in verbose mode or silent mode:

## Verbose Mode:

```bassh
./kmapper.py <Country_kobo_directory> <standard_template_path.xlsx> <output_directory> --verbose
```

### Current flags available: 

- kobo_directory : Directory containing Countries KoboToolbox files.
- standard_template_path  : Path to the standard survey template xlxs.
- output_directory : Directory to save discrepancy reports
  
- **--verbose** : Enable verbose logging.
- **--threshold** : Threshold as intiger for approximate matching (default: 90).
- **--append** : Append to existing reports instead of overwriting.
    
## Silent Mode:

```bassh
./kmapper.py tests/CountryKobo/ tests/REACH_2024_MSNA-kobo-tool_draft_v9.xlsx tests/
```

##ToDO : 
    - Add the flask implementation for the webUI.
