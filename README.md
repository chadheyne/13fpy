# 13F Text Parser

----------

## Parse 13F filings into csv format

###Works with comma delimited, tab delimited, and pseudo fixed width 13F filings.

----------

*   move_files.py 

    Requires:  

    * File containing CIKs and dates that are of interest 
    * Directory of already downloaded universe of 13F filings  

    Generates:  

    * Moves filings from desired CIKs and dates to separate directory for processing.
    * Summary file containing information on:  

        * Path, year, date, CIK, and size of files moved
        * Path, year, date, CIK, and size of all filings in directory   

----------

*   header_info.py  

    Requires:  

    * Directory containing raw 13F filings that should be processed.

    Generates:  

    * Csv file containing parsed header information for each of the filings and additional identifying information to be used in merging data.

    The following columns are
    imperfectly parsed:  

    * Number of other Included Managers
    * Form 13F Information Table Entry Total
    * Form 13F Information Table Value Total  

    The 13F filings are inconsistent in the language and formatting of these variables resulting in
    irregularities

----------

*   table_extract.py  
    Requires:  

    * CUSIP file from Wrds. 
        * Can include multiple CUSIP files and make the matching more liberal by    allowing CUSIPs to have leading zeros trimmed and by considering 6, 8, and 9 digit CUSIPs.
    * patterns.csv which contains regular expressions to match specific types of strings. In particular:  

        * focuses on finding possible CUSIP matches, 
        * skipping lines in the file that clearly do not have data
          but incorrectly are picked up as CUSIPs generating false positives,
        * determining very liberally the
        possibility of a given observation being an option.
    * Directory containing list of raw filings to be parsed.
    * table_templates.py   

        * contains parsing functions for multiple popular 13F formats.  

    Generates:  

    * Csv file for each filing detailing the holdings reported within:
        * Name of company being held and the holding type 
        * CUSIP of company being held
        * Value and number of shares of company being held
        * Possibility of being an option holding 

----------

*   create_merged.py  
    Requires:  

    * Directory of already processed data  

    Generates:  

    * Csv file containing all observations that were processed.
    * Csv file containing all observations that might be option holdings with an additional flag to determine accuracy.
    * Csv file containing all observations that are "clearly" option holdings.

    Notes:  

    * Look at flagged option lines and assess likelihood of being a true option and integrity of the observation by flagging if:  

        * Skip rows that have any "-999999" which is universal flag for parsing error.
        * Length of name > 35 (Typically happens when CUSIP is incorrectly flagged in value or shares column, resulting in a bad split)
        * Missing value or shares data (Typically happens when raw row contained bad characters or there was no space between the value and shares)
        * CUSIP is the same as value or shares (Typically happens when using liberal matching rules for CUSIP which can generate false positives for the CUSIP. Will only reach the value or shares column if the actual CUSIP is not in the CUSIP dictionary).
        * Option column is either "CLA", "PU", "CL A", or "CL" or there are any non alphanumeric characters in the option column. (Removes several false positives, such as CLASS A shares, etc.)  

----------

### Parsing steps: 

1. Each filing is first run through a function determining the eligibility of a given data row by first looking for possible CUSIP matches and then verifying the CUSIP exists in the dictionary of CUSIPs.   
The eligible rows are written to a csv file with a column containing the assumed CUSIP and the full line.
The remaining rows are sent to a separate file which can be examined to assess accuracy of the algorithm.  

2. If the csv containing eligible rows already exists, the data is read from the csv and sent to the parsing algorithm. Otherwise, it relies on the return value of the previous function for parsing purposes.  
The master parser will look at each data line, attempt to split the data on the CUSIP creating a list of
before CUSIP data (Company name and type of holding) and after CUSIP data (Value of holding, number of shares being
held, voting rights, etc.). The algorithm also determines which of csv, tab, and pseudo fixed width formats fits
the particular filing and ships it off to that parser.  

3. Parsing functions  
    * Tab delimited files:  
    Before any actual parsing begins, the function loops through the before and after CUSIP sections separately,
    and attempts to "guess" which columns are most frequently empty. This naive splitting approach is used as a last resort.
    Loop through each line of data, first determining whether the observation is possibly an option holding.  

        The before CUSIP data is split into two fields (company name and holding type) based on two approaches:  

        * Regular expression containing tab then word character which should indicate a column delimiter.
        * The most frequently occupied column of a tab from the naive approach.
        * If the naive approach fails, assign the holding type to "-999999" and company name to the rest.  

        The after CUSIP data is split into two fields (value and shares) based on two approaches:  

        * Regular expression containing two sets of digit characters separated by a tab.
        * Splitting the line on tab delimiters and taking the first two arguments.
        * If these approaches fail, value is assigned the entire string and shares is assigned "-999999"  

        Finally, write a csv file containing the above fields and print the flagged option fields to a log file.  

    * Comma delimited files:  
    If there are at least 5 commas (ignoring commas within a field) in the line, then the data is split into
    Name, CUSIP, value, shares, and the remainder of the line. Possible option rows are flagged by searching
    the entire line and the resulting data is saved to a csv file while option data is also printed to a log.      

    * Pseudo fixed width files:  
    The algorithm first attempts to find the most likely column splits by using regular expressions and then
    loops through each line first dividing the before CUSIP data into two fields (company name and holding type)
    based on two approaches:  

        * Regular expression for multiple spaces preceding a character.
        * Most likely column splitter from before.
        * If these approaches fail, name is assigned the entire string and holding type is assigned "-999999"  

        The after CUSIP data is split into two fields using three approaches:  

        * Regular expression for two groups of digit characters separated by multiple spaces.
        * Regular expression for two groups of digit characters separated by a single space.
        * Naively splitting on most likely column.
        * If these approaches fail, value is assigned the entire string and number of shares is assigned "-999999"          

    * HTML files:  
    Not implemented yet. Very few filings use HTML tables for their data in the current dataset and the ones that do
    have no option holdings.
