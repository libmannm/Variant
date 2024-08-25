from datetime import datetime

from Variant_Filter import filterer
from Variant_Processing2 import Process
from Variant_Export2 import variant_final

def variant(data_folder, timestamp_folder, results_folder, 
            time = 5, 
            JSON_Path = f"Variant_{datetime.now().date()}.json", 
            CSV_Path = f"Variant_{datetime.now().date()}.csv", 
            error_out = f"Variant_Error_{datetime.now().date()}.txt"):
    """
    Calls all of the steps in the processing pipeline from one function
    
    Parameters
    ----------
    data_folder : The path to the folder with all of the EyeMotions outputs, this is also where the filtered files will go.  It is alright for other files to be in this folder as long as they are not .csv files
    timestamp_folder : The path to the folder containing all of the timestamp data
    results_folder : The path to the folder where the results and error messages will be exported
    time : The amount of time (seconds) after the true beginning of the trial before the truncated data starts
    JSON_Path : The name of the file where the JSON will be stored, must end in .json
        The default is f"{datetime.now().date()}.json"
    CSV_Path : The name of the file where the CSV output will be stored, must end in .csv
        The default is f"{datetime.now().date()}.csv"
    """
    
    JSON_Path = results_folder + JSON_Path
    CSV_Path = results_folder + CSV_Path
    
    filterer(data_folder)  ###Creates duplicates of each participant's data that has been reduced to the important features and processed (blinks etc.)
    processed_data = Process(data_folder = data_folder, 
                   timestamp_folder = timestamp_folder, 
                   results_folder = results_folder, 
                   time = 5) ###From the filtered data, assemble and calculate all interesting data; export into an intermediary JSON
    
    
    variant_final(CSV_Path, processed_data.data) ###Conzvert the JSON to a .csv for easier interpretation/further analysis



variant(data_folder = "D:/Research/Kaiyo/Code/Variants/Data/",
        timestamp_folder = "D:/Research/Kaiyo/Code/Variants/Data/Timestamps/",
        results_folder = "D:/Research/Kaiyo/Code/Variants/Results/",
        time = 5)