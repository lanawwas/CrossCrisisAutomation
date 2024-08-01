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