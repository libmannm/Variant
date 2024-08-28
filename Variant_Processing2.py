import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore")

class Process():
    def __init__(self, data, row, time = 5): #time refers to time in seconds after the start of the trial before the beginning of the truncated period
        
        self.data = {}

        #for i,row in enumerate(tqdm(directories)):
            
        self.ID = str(row[0])+row[1]  #i.e. 103J
                    
        self.data[self.ID] = {"750 - 800":{"times":{}},
                          "750 - 400":{"times":{}},
                          "750 - 200":{"times":{}},
                          "1000 - 800":{"times":{}},
                          "1000 - 400":{"times":{}},
                          "1000 - 200":{"times":{}}}
        
        ts_path = row[3]
        
        #self.data_array = pd.read_csv(data_path, usecols=["Timestamp","Pupil"]).to_numpy()
        self.data_array = data[["Timestamp","Pupil"]].to_numpy()
        self.data_array = np.hstack((np.arange(self.data_array.shape[0]).reshape(-1,1), self.data_array))  #Add an index column
        
        self.key_list = self.timestamp_times(ts_path)  #Gathers the beginning and end times for each condition
        
        self.check = False #This variable tells Variant.py if an error occured or not
        if len(self.key_list) == 0:
            del self.data[self.ID]
            self.error_line = f"{self.ID}: Missing Trials"
            return
        
        if np.nanmean(data["Pupil"])*0 != 0:
            del self.data[self.ID]
            self.error_line = f"{self.ID}: All pupil values invalid"
            return
        self.check = True
        
        self.NaN_list = data[["NaN"]]
        
        prev_key = ""
        for key in self.key_list:
            self.find_timestamps(key, prev_key, time)  #Finds all relevant indices given the times gathered previously
            self.calculate(key)  #Uses the found indicies to subset data_array and calculate baseline, truncated etc. values
            prev_key = key
        
        self.error_count()
    
    def timestamp_times(self, ts_path):
        try: #There were inconsistencies with the naming of certain columns in the original data
            timestamp = pd.read_csv(ts_path, usecols=["TrialISI","StimDur","arrow_disp.started", "arrow_disp.stopped"]).to_numpy()
        except:
            timestamp = pd.read_csv(ts_path, usecols=["TrialISI","StimDur","letter_disp.started", "letter_disp.stopped"]).to_numpy()
        
        timestamp = timestamp[(timestamp[:,0]*0 == 0) & (timestamp[:,2] != "None")] #Filters for missing rows and NaN values
        
        key_list = []
        ISI = 0
        stimDur = 0
        for row in timestamp:  #Important for subsequent searches that this list be made in the order that it was recorded in data
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

            timestamp_subset = timestamp[(timestamp[:,0] == ISI) & (timestamp[:,1] == stimDur)] #Supset all the timestamp data corresponding to a given trial identifier

            self.data[self.ID][key]["times"]["start_time"] = np.min(timestamp_subset[:,2].astype(float))*1000
            self.data[self.ID][key]["times"]["end_time"] = np.max(timestamp_subset[:,3].astype(float))*1000
    
        return key_list    
    
    def find_timestamps(self, key, prev_key, trunc_time_in):        
        start_time = self.data[self.ID][key]["times"]["start_time"]
        end_time = self.data[self.ID][key]["times"]["end_time"]
        trunc_time = start_time + trunc_time_in*1000
        baseline_time = start_time - 5000
        
        #Find all relevant times per identifier in the EyeMotions data (baseline start, trial start, truncated start, trial end)
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
        
        #To avoid repeatedly searching the same data, the for loop restarts after the known end point of the previous trial - This is why key_list must be in order
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
        
        self.data[self.ID][key]["times"]["length"] = end_i - start_i
        
        self.data[self.ID][key]["Baseline_Ave"] = np.nanmean(self.data_array[baseline_i:start_i,2])
        self.data[self.ID][key]["Baseline_Max"] = np.nanmax(self.data_array[baseline_i:start_i,2])
        
        self.data[self.ID][key]["Truncated_Ave"] = np.nanmean(self.data_array[trunc_i:end_i,2])
        self.data[self.ID][key]["Truncated_Max"] = np.nanmax(self.data_array[trunc_i:end_i,2])
        
        self.data[self.ID][key]["Total_Ave"] = np.nanmean(self.data_array[start_i:end_i,2])
        self.data[self.ID][key]["Total_Max"] = np.nanmax(self.data_array[start_i:end_i,2])
        
        self.data[self.ID][key]["Average_Difference"] = self.data[self.ID][key]["Total_Ave"] - self.data[self.ID][key]["Baseline_Ave"]
        self.data[self.ID][key]["Maximum_Difference"] = self.data[self.ID][key]["Total_Max"] - self.data[self.ID][key]["Baseline_Max"]
        
        self.data[self.ID][key]["NaN_Rate"] = {}
        NaN_count = int(np.sum(self.NaN_list[start_i:end_i]))
        self.data[self.ID][key]["NaN_Rate"]["count"] = NaN_count
        self.data[self.ID][key]["NaN_Rate"]["ratio"] = float(NaN_count/(end_i - start_i))
    
    def error_count(self):
        NaNs = 0
        length = 0
        for key in self.key_list:
            NaNs = NaNs + self.data[self.ID][key]["NaN_Rate"]["count"]
            length = length + self.data[self.ID][key]["times"]["length"]
        
        self.data[self.ID]["Error"] = {}
        self.data[self.ID]["Error"]["Total_Length"] = length
        self.data[self.ID]["Error"]["NaNs"] = NaNs
        self.data[self.ID]["Error"]["Ratio"] = NaNs/length