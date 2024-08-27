from datetime import datetime
from tqdm import tqdm
import numpy as np
import json

from Variant_Filter import filterer, find_directories
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
    error_out = results_folder + error_out
    JSON_Path = results_folder + JSON_Path
    CSV_Path = results_folder + CSV_Path
    
    directories, error_list  = find_directories(data_folder, timestamp_folder)
    
    dictionary = {}
    
    for row in tqdm(directories):
        data_file = row[2]
        
        df = filterer(data_file)  ###Creates duplicates of each participant's data that has been reduced to the important features and processed (blinks etc.)
        processed_data = Process(data = df, 
                       row = row, 
                       time = 5) ###From the filtered data, assemble and calculate all interesting data; export into an intermediary JSON
        
        if processed_data.check == True:
            dictionary.update(processed_data.data)
        else:
            error_list.append(processed_data.error_line)
        
        
    variant_final(CSV_Path, dictionary) ###Conzvert the JSON to a .csv for easier interpretation/further analysis
    
    with open(error_out, "w") as file:
        for item in error_list:
            file.write(item + "\n")
    
    with open(JSON_Path, "w") as out_file:
        json.dump(dictionary, out_file, indent=4)
    
    return(dictionary)
    
a = variant(data_folder = "M:/Research/Kaiyo/Code/Variants/Data/",
        timestamp_folder = "M:/Research/Kaiyo/Code/Variants/Data/Timestamps/",
        results_folder = "M:/Research/Kaiyo/Code/Variants/Results/",
        time = 5)