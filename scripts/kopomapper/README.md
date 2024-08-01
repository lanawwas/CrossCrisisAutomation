Special Case Handling for type:

    The script now skips rows where the type is one of the special types (begin_group, end_group, begin_repeat, end_repeat) during the name matching process. This prevents incorrect matches due to multiple occurrences of these types.

Independent Column Comparison:

    Each column defined in SURVEY_COLUMNS_TO_COMPARE and CHOICES_COLUMNS_TO_COMPARE is compared independently. Discrepancies are logged for each column separately.

How It Works:

    Loading Files:
        The script loads the KoboToolbox survey files for each country and the standard template.
    Extracting Variables:
        The script extracts the relevant columns from both the country files and the standard template.
    Comparing Data:
        For the 'survey' tab, it compares each row in the standard template with the corresponding row in the country file based on the 'name' column, except for rows with special types.
        For the 'choices' tab, it performs a similar comparison based on the 'name' and 'list_name' columns.
    Generating Reports:
        The script generates individual discrepancy reports for each country and a master report combining all discrepancies.

Set Execute Permission:
To make the script executable, you need to set the execute permission. You can do this using the chmod command in the terminal:

```sh
chmod +x kmapper.py
```
Running the Script

You can now run the script in verbose mode or silent mode:

Verbose Mode:

```sh
./kmapper.py tests/CountryKobo/ tests/REACH_2024_MSNA-kobo-tool_draft_v9.xlsx tests/ --verbose
```
Silent Mode:

```sh
./kmapper.py tests/CountryKobo/ tests/REACH_2024_MSNA-kobo-tool_draft_v9.xlsx tests/
```

##ToDO : 
    - Add the flask implementation for the webUI.