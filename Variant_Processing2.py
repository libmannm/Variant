import os
import json
import pandas as pd
import numpy as np
from tqdm import tqdm
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

class Process():
    def __init__(self, data_folder, timestamp_folder, results_folder, JSON_out = f"Variant_{datetime.now().date()}.json", error_out = f"Variant_Error_{datetime.now().date()}.txt", time = 5):
        error_list = []
        
        directories, missing_data = self.find_directories(data_folder, timestamp_folder)
        
        error_list += missing_data
        
        self.data = {}

        for i,row in enumerate(tqdm(directories)):
            
            self.ID = str(row[0])+row[1]
                        
            self.data[self.ID] = {"750 - 800":{"times":{}},
                              "750 - 400":{"times":{}},
                              "750 - 200":{"times":{}},
                              "1000 - 800":{"times":{}},
                              "1000 - 400":{"times":{}},
                              "1000 - 200":{"times":{}}}
            
            data_path = row[2]
            ts_path = row[3]
            
            self.data_array = pd.read_csv(data_path, usecols=["Timestamp","Pupil"]).to_numpy()
            self.data_array = np.hstack((np.arange(self.data_array.shape[0]).reshape(-1,1), self.data_array))
            
            self.key_list = self.timestamp_times(ts_path)  #Gathers the beginning and end times for each condition
            
            if len(self.key_list) == 0:
                del self.data[self.ID]
                error_list.append(f"{self.ID}: Missing Trials")
                continue
            
            prev_key = ""
            for key in self.key_list:
                self.find_timestamps(key, prev_key, time)  #Finds all relevant indices given the times gathered previously
                self.calculate(key)  #Uses the found indicies to subset data_array and calculate baseline, truncated etc. values
                prev_key = key
                
            out_file = open(results_folder + JSON_out, "w")
            json.dump(self.data, out_file, indent = 4)
            
            with open(results_folder + error_out, "w") as file:
                for item in error_list:
                    file.write(item + "\n")
                
    def find_directories(self, data, timestamp):
        temp_data_path = os.listdir(data)
        data_path = []
        
        for file_path in temp_data_path:
            if "filter" in file_path and ".csv" in file_path:
                data_path.append(file_path)
        
        ts_path = os.listdir(timestamp)
        
        missing_data = []
        
        directories = np.empty([218,4],dtype = object)
        
        i = 0
        
        for code in ["Arrow", "Letter"]:
            letter_code = {"Arrow":"I", "Letter": "J"}
            for number in range(1,110):
                number_code = "_" + str(number) + "CE"
                temp_data_path = ""
                temp_ts_path = ""
                
                for path in data_path:      
                    if code in path and number_code in path:
                        temp_data_path = path
                        break
                
                for path in ts_path:
                    if code in path and number_code in path:
                        temp_ts_path = path
                        break
                
                if temp_data_path != "" and temp_ts_path != "":
                    directories[number-1+i, 0] = number
                    directories[number-1+i, 1] = letter_code[code]
                    directories[number-1+i, 2] = data + temp_data_path
                    directories[number-1+i, 3] = timestamp + temp_ts_path
                else:
                    directories[number-1+i,0] = 99999
                    if temp_data_path == "" and temp_ts_path == "":
                        missing_data.append(f"{number}{code}: Missing Data and Timestamp")
                    elif temp_data_path == "":
                        missing_data.append(f"{number}{code}: Missing Data")
                    else:
                        missing_data.append(f"{number}{code}: Missing Timestamp")
            i = 109
            
        directories = directories[directories[:,0]!=99999]
        return directories, missing_data
    
    def timestamp_times(self, ts_path):
        try:
            timestamp = pd.read_csv(ts_path, usecols=["TrialISI","StimDur","arrow_disp.started", "arrow_disp.stopped"]).to_numpy()
        except:
            timestamp = pd.read_csv(ts_path, usecols=["TrialISI","StimDur","letter_disp.started", "letter_disp.stopped"]).to_numpy()
        
        timestamp = timestamp[(timestamp[:,0]*0 == 0) & (timestamp[:,2] != "None")]
        
        key_list = []
        ISI = 0
        stimDur = 0
        for row in timestamp:
            if row[0] != ISI or row[1] != stimDur:
                ISI = int(row[0])
                stimDur = int(row[1])
                key_list.append(f"{ISI} - {stimDur}")
        
        if len(key_list) != 6:
            return []
        
        self.data[self.ID]["key_order"] = key_list
        
        for key in key_list:
            ISI = int(key.split(" - ")[0])
            stimDur = int(key.split(" - ")[1])

            timestamp_subset = timestamp[(timestamp[:,0] == ISI) & (timestamp[:,1] == stimDur)]
            
            #print(timestamp_subset[:,2],type(np.min(timestamp_subset[:,2])), np.min(timestamp_subset[:,2]), "\n\n\n\n")
            
            self.data[self.ID][key]["times"]["start_time"] = np.min(timestamp_subset[:,2].astype(float))*1000
            self.data[self.ID][key]["times"]["end_time"] = np.max(timestamp_subset[:,3].astype(float))*1000
    
        return key_list    
    
    def find_timestamps(self, key, prev_key, trunc_time_in):        
        start_time = self.data[self.ID][key]["times"]["start_time"]
        end_time = self.data[self.ID][key]["times"]["end_time"]
        trunc_time = start_time + trunc_time_in*1000
        baseline_time = start_time - 5000
        
        if prev_key == "":
            with np.nditer(self.data_array, flags=['external_loop', 'refs_ok'], order='C') as it:
                for i,row in enumerate(it):
                    if row[1] > baseline_time:
                        self.data[self.ID][key]["times"]["baseline_index"] = int(row[0])
                        self.data[self.ID][key]["times"]["baseline_check"] = self.data_array[int(row[0]),1]
                        break                    
                for i,row in enumerate(it):
                    if row[1] > start_time:
                        self.data[self.ID][key]["times"]["start_index"] = int(row[0])
                        self.data[self.ID][key]["times"]["start_check"] = self.data_array[int(row[0]),1]
                        break
                for i,row in enumerate(it):
                    if row[1] > trunc_time:
                        self.data[self.ID][key]["times"]["trunc_index"] = int(row[0])
                        self.data[self.ID][key]["times"]["trunc_check"] = self.data_array[int(row[0]),1]
                        break
                for i,row in enumerate(it):
                    if row[1] > end_time:
                        self.data[self.ID][key]["times"]["end_index"] = int(row[0])
                        self.data[self.ID][key]["times"]["end_check"] = self.data_array[int(row[0]),1]
                        break
                    
        else:
            start_search = self.data[self.ID][prev_key]["times"]["end_index"] + 1
            with np.nditer(self.data_array[start_search:,:], flags=['external_loop', 'refs_ok'], order='C') as it:
                for i,row in enumerate(it):
                    if row[1] > baseline_time:
                        self.data[self.ID][key]["times"]["baseline_index"] = int(row[0])
                        self.data[self.ID][key]["times"]["baseline_check"] = self.data_array[int(row[0]),1]
                        break                    
                for i,row in enumerate(it):
                    if row[1] > start_time:
                        self.data[self.ID][key]["times"]["start_index"] = int(row[0])
                        self.data[self.ID][key]["times"]["start_check"] = self.data_array[int(row[0]),1]
                        break
                for i,row in enumerate(it):
                    if row[1] > trunc_time:
                        self.data[self.ID][key]["times"]["trunc_index"] = int(row[0])
                        self.data[self.ID][key]["times"]["trunc_check"] = self.data_array[int(row[0]),1]
                        break
                for i,row in enumerate(it):
                    if row[1] > end_time:
                        self.data[self.ID][key]["times"]["end_index"] = int(row[0])
                        self.data[self.ID][key]["times"]["end_check"] = self.data_array[int(row[0]),1]
                        break
        
    def calculate(self, key):
        baseline_i = self.data[self.ID][key]["times"]["baseline_index"]
        start_i = self.data[self.ID][key]["times"]["start_index"]
        trunc_i = self.data[self.ID][key]["times"]["trunc_index"]
        end_i = self.data[self.ID][key]["times"]["end_index"]
        
        self.data[self.ID][key]["Baseline_Ave"] = np.nanmean(self.data_array[baseline_i:start_i,2])
        self.data[self.ID][key]["Baseline_Max"] = np.nanmax(self.data_array[baseline_i:start_i,2])
        
        self.data[self.ID][key]["Truncated_Ave"] = np.nanmean(self.data_array[trunc_i:end_i,2])
        self.data[self.ID][key]["Truncated_Max"] = np.nanmax(self.data_array[trunc_i:end_i,2])
        
        self.data[self.ID][key]["Total_Ave"] = np.nanmean(self.data_array[start_i:end_i,2])
        self.data[self.ID][key]["Total_Max"] = np.nanmax(self.data_array[start_i:end_i,2])
        
        self.data[self.ID][key]["Average_Difference"] = self.data[self.ID][key]["Total_Ave"] - self.data[self.ID][key]["Baseline_Ave"]
        self.data[self.ID][key]["Maximum_Difference"] = self.data[self.ID][key]["Total_Max"] - self.data[self.ID][key]["Baseline_Max"]
        
# A = Process(data_folder = "D:/Research/Kaiyo/Code/Variants/Data/",
#             timestamp_folder = "D:/Research/Kaiyo/Code/Variants/Data/Timestamps/",
#             results_folder= "D:/Research/Kaiyo/Code/Variants/Results/",
#             time = 5)