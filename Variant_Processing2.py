import os
import json
import pandas as pd
import numpy as np
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore")

class Process():
    def __init__(self, data_folder, timestamp_folder, j_path, time = 23):
        error_list = []
        
        directories, missing_data = self.find_directories(data_folder, timestamp_folder)
        
        error_list += missing_data
        
        global data
        data = directories
        #print(error_list)
        
        self.data = {}

        for i,row in enumerate(tqdm(directories)):
            
            self.ID = str(row[0])+row[1]
            
            #self.key_list = ["750 - 800","750 - 400","750 - 200","1000 - 800","1000 - 400","1000 - 200"]
            
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
            prev_key = ""
            for key in self.key_list:
                self.find_timestamps(key, prev_key)  #Finds all relevant indices given the times gathered previously
                prev_key = key
                
                
                
        global data_dict
        data_dict = self.data
                
                
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
        
        global timestamp2
        timestamp2 = timestamp
        
        for key in key_list:
            ISI = int(key.split(" - ")[0])
            stimDur = int(key.split(" - ")[1])

            timestamp_subset = timestamp[(timestamp[:,0] == ISI) & (timestamp[:,1] == stimDur)]
            
            #print(timestamp_subset[:,2],type(np.min(timestamp_subset[:,2])), np.min(timestamp_subset[:,2]), "\n\n\n\n")
            
            self.data[self.ID][key]["times"]["start_time"] = np.min(timestamp_subset[:,2].astype(float))*1000
            self.data[self.ID][key]["times"]["end_time"] = np.max(timestamp_subset[:,3].astype(float))*1000
    
        return key_list    
    
    def find_timestamps(self, key, prev_key):        
        start_time = self.data[self.ID][key]["times"]["start_time"]
        end_time = self.data[self.ID][key]["times"]["end_time"]
            
        if prev_key == "":
            with np.nditer(self.data_array, flags=['external_loop', 'refs_ok'], order='C') as it:
                
                for i,row in enumerate(it):
                    #if type(row[0]) == str or type(start_time) == str:
                        #print(self.ID,key,row[0], start_time)
                    if row[1] > start_time:
                        self.data[self.ID][key]["times"]["start_index"] = int(row[0])
                        self.data[self.ID][key]["times"]["start_check"] = self.data_array[int(row[0]),1]
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
                    if row[1] > start_time:
                        self.data[self.ID][key]["times"]["start_index"] = int(row[0])
                        self.data[self.ID][key]["times"]["start_check"] = self.data_array[int(row[0]),1]
                        break
                for i,row in enumerate(it):
                    if row[1] > end_time:
                        self.data[self.ID][key]["times"]["end_index"] = int(row[0])
                        self.data[self.ID][key]["times"]["end_check"] = self.data_array[int(row[0]),1]
                        break
        
A = Process("M:/Research/Kaiyo/Code/Variants/Data/", "M:/Research/Kaiyo/Code/Variants/Data/Timestamps/", "M:/Research/Kaiyo/Code/Variants/Results/", 23)