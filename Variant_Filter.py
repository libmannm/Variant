import pandas as pd
import numpy as np
import os
import warnings

warnings.filterwarnings("ignore")  #The formatting of the EyeMotions data files results in a variety of inconsequential intake errors

def find_directories(data_folder, timestamp_folder):
    temp_data_path = os.listdir(data_folder)
    data_path = []
    
    for file_path in temp_data_path:
        if ".csv" in file_path:
            data_path.append(file_path)
    
    ts_path = os.listdir(timestamp_folder)
    
    missing_data = []
    
    directories = np.empty([218,4],dtype = object) # columns: participant number, letter code (I or J), data path, timestamp path
    
    i = 0
    
    for code in ["Arrow", "Letter"]:
        letter_code = {"Arrow":"I", "Letter": "J"}
        for number in range(1,110):
            number_code = "_" + str(number) + "CE"
            temp_data_path = ""
            temp_ts_path = ""
            
            #Find each data file and then pair with the corresponding timestamp file
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
                directories[number-1+i, 2] = data_folder + temp_data_path
                directories[number-1+i, 3] = timestamp_folder + temp_ts_path
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
    
def filterer(data_file):
    df = pd.read_csv(data_file, usecols = [0]).to_numpy()
    
    for i,j in enumerate(df):
        if j == "#DATA":
            break
    
    i = i+2  #Establish where the header ends and data begins

    data = pd.read_csv(data_file, skiprows = i, usecols=["Timestamp","ET_PupilLeft","ET_PupilRight"]).to_numpy()

    data = data[data[:,1]*0 == 0]  #Ensures no blank rows are included
    data = data[data[:,2]*0 == 0]
    
    A = filtering(data)
    return A.df
    

class filtering():
    def __init__(self, data):
        self.df = pd.DataFrame(data[:,0], columns = ["Timestamp"])
        self.data = data[:,1:3]
        self.size = np.shape(self.data)[0]
        
        self.lrmerge() #Averages left and right eye sizes into one column
        
        self.NaNs = []
        for i,j in enumerate(self.data):
            if j*0 != 0:
                self.NaNs.append(i)
        
        self.outliers() #Finds outliers via IQR and marks them for deletion
        self.crop()  #Actually deletes data that has been marked for deletion in the past steps
        
        self.find_blinks()  #Identifies blinks and blink borders from patterns in NaNIndex and adds them to NaNIndex
        self.crop()        
        
        if self.data[-1] * 0 != 0: #the pandas interpolate function struggles with edge cases
            self.data[-1] = np.nanmean(self.data)
        if self.data[0] * 0 != 0:
            self.data[0] = np.nanmean(self.data)
        
        self.NaNArray() #Finds total number of NaN's per participant and per trial to be used for error columns
        
        self.df["Pupil"] = self.data
        self.df["Pupil"] = self.df["Pupil"].interpolate(method = "pchip") #pchip was qualitatively the best and most consistent
        self.df["NaN"] = self.nan_array #If pupil was at any point a NaN at a certain index, the value of this column at that index will be 1
        
    def lrmerge(self):
        #EyeMotions stores invalid measurements as -1
        #This function finds all instances of one eye being invalid while the other is valid to interpolate data for the invalid measurement before averaging both columns
        for i in range(self.size):
            if self.data[i,0] > 0 and self.data[i,1] == -1: 
                j = 1
                while self.data[i-j,1] == -1 or self.data[i-j,0] == -1:
                    j += 1
                change = self.data[i,0] - self.data[i-j,0] 
                self.data[i,1] = self.data[i-j,1] + change
            elif self.data[i,1] > 0 and self.data[i,0] == -1:
                j = 1
                while self.data[i-j,1] < 0 or self.data[i-j,0] == -1:
                    j += 1
                change = self.data[i,1] - self.data[i-j,1] 
                self.data[i,0] = self.data[i-j,0] + change
        
        self.data = np.mean(self.data, axis = 1)
        self.data[self.data < 0] = np.nan
    
    def outliers(self):
        quantile = np.nanquantile(self.data, [0,0.25,0.5,0.75,1])
        IQR = quantile[3]-quantile[1]
        upper_fence = quantile[3]+2.5*IQR #This boundary is intentionally very conservative
        lower_fence = quantile[1]-2.5*IQR
        
        self.NaNIndex = []
        for i,val in enumerate(self.data):
            if val < lower_fence or val > upper_fence:
                self.NaNIndex.append(i)
    
    
    def find_blinks(self):
        blink_start = []
        blink_stop = []
        cu = 0
        
        #Looks through NaNIndex for between 9 and 100 consecutive NaN values (45ms - 500ms) as generally suggest a blink rather than random error
        for i, NaN in enumerate(self.NaNIndex[:-1]):
            if NaN+1 == self.NaNIndex[i+1] and i < len(self.NaNIndex)-2:
                cu += 1
            else:
                if cu > 9 and cu < 100:
                    blink_stop.append(i)
                    blink_start.append(i-cu)
                cu = 0
                
        #Goes through the beginning and end of each blink and filters the immediate data monotonically
        for j in range(len(blink_start)):    
            ind = self.NaNIndex[blink_start[j]]
            pupil_val = self.data[ind]
            while self.monoCompare(pupil_val,ind-1):
                self.NaNIndex.append(ind)
                ind = ind - 1
                pupil_val = self.data[ind]
            
        for j in range(len(blink_stop)):    
            ind = self.NaNIndex[blink_stop[j]]
            pupil_val = self.data[ind]
            while self.monoCompare(pupil_val,ind+1):
                self.NaNIndex.append(ind)
                ind += 1
                pupil_val = self.data[ind]
    
    def NaNArray(self):
        self.nan_array = np.zeros_like(self.data)
        self.NaNIndex = self.NaNIndex + self.NaNs
        
        for i in self.NaNIndex:
            self.nan_array[i] = 1
        
    def crop(self):
        for j in self.NaNIndex:
            self.data[j] = np.nan

    def monoCompare(self,first,second):
        if first > self.data[second]:
            return False
        elif second+1 == len(self.data):
            return False
        else:
            return True
