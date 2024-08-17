from datetime import datetime

from Variant_Filter import filterer
from Variant_Processing import process

def variant(data_folder, timestamp_folder, results_folder, time, JSON_Path = f"{datetime.now().date()}.json", CSV_Path = f"{datetime.now().date()}.csv"):
    """
    Calls all of the steps in the processing pipeline from one function
    
    Parameters
    ----------
    data_folder : The path to the folder with all of the EyeMotions outputs, this is also where the filtered files will go.  It is alright for other files to be in this folder as long as they are not .csv files
    timestamp_folder : The path to the folder containing all of the timestamp data
    results_folder : The path to the folder where the results and error messages will be exported
    time : The amount of time not used to calculate baseline, see README or article for explanation
    JSON_Path : The name of the file where the JSON will be stored, must end in .json
        The default is f"{datetime.now().date()}.json"
    CSV_Path : The name of the file where the CSV output will be stored, must end in .csv
        The default is f"{datetime.now().date()}.csv"
    """
    JSON_Path = results_folder + JSON_Path
    CSV_Path = results_folder + CSV_Path
    
    filterer(data_folder)  ###Creates duplicates of each participant's data that has been reduced to the important features and processed (blinks etc.)
    process(23, data_folder, JSON_Path) ###From the filtered data, assemble and calculate all interesting data; export into an intermediary JSON
    VariantFinal(JSON_Path, CSV_Path, data_folder) ###Convert the JSON to a .csv for easier interpretation



variant(data_folder = "D:/Research/Kaiyo/Code/Variants/Data/",
        timestamp_folder = "D:/Research/Kaiyo/Code/Variants/Data/Timestamps/",
        results_folder = "D:/Research/Kaiyo/Code/Variants/Results/",
        time = 23)