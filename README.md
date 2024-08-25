# Variant

Developed as part of TK, this series of scripts processes a combination of raw data from an EyeMotions tracker and defined experimental parameters to output data for later statistical analysis.  In particular, these scripts calculate pupil size metrics across different experimental conditions.  While these scripts were designed for a specific task, the modules and methods may be more broadly applicable.

## Prerequisite Folder Organization & Input Format

The script requires the existence of 3 designated folders containing the EyeMotions data (data_folder), the trial parameter data (timestamp_folder), and eventually the results (results_folder).  These folders do not need to be in a particular order (no required nesting etc.).  As a result, it may be helpful to define folders in the script with global paths.  Having the 2 data folders contain only their respective files is also recommended. 

<ins>Folder Contents</ins>
- data_folder/EyeMotions
  - Naming: Should all be .csv files with the naming scheme "{index number}_{participant number}CE {Letter or Arrow} {mm-dd-yy} {hours}h{minutes}m.csv" i.e. 001_109CE Letter 03-08-22 14h22m.csv
  - File characteristics:
    - The file should contain approximately 30 lines of header ending with the line "#DATA"
    - Among others, the file should contain the columns "Timestamp", "ET_PupilLeft", and "ET_PupilRight" in the row immediately under "#DATA"

## Script Output
The script will output 3 files: two files of processed data (a .csv and a .json) and a .txt that tracks any errors throughout the processing pipeline.  By default, these files are all named as derivatives of the date the script was run, so it is recommended to provide the script with alternative specific names if you plan on running the script multiple times on a given day.

- .csv Results
  - The .csv output is the most reduced form of the data.  It consists of 6 rows per participant -- one per variant condition.  Each row contains participant/condition identifiers and 8 metrics: The maximum and average pupil size for the baseline period, the total trial period, and the truncated trial period as well as the differences between the maximums and averages for the baseline and total trial periods.
- .json Results
  - In addition to the data required for the .csv, the .json also contains metadata for each trial such as the length of the trial, the specific timestamps of each condition, and the order in which the conditions were presented.
  - The dictionary is generally structured as follows: "Participant + Letter Code" : {"Variant Condition" : {"times: {start time, start index etc.}, data for .csv}}
- .txt Errors
  - A simple list of each missing participant and the reason for exclusion (i.e. missing timestamp data, missing data file, or both)


## Running the Script
From this repository, it should only be necessary to interact with the script "Variant.py".  Once all variables and folder paths are defined in Variant.py, it will call all necessary classes and functions from the other scripts.  It is important though to ensure that all scripts are available to your environment.  This can usually be done by simply keeping all scripts in the same folder.  This script is intended to be run in an IDE rather than on a command line. However, it is well structured for adaptation to a callable script if it fits your needs.

<ins>General Process</ins>

1. Gather the raw pupil data from the EyeMotions files, filter them for outliers and blinks, average the pupil values, and store as a "filtered" .csv.
2. Using the timestamp files, locate the beginning and end of each trial for each participant within the filtered data.
3. Calculate all wanted metrics from these data subsets.
4. From this data (the .json) reformat the relevant information into a .csv.
