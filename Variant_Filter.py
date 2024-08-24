import pandas as pd
import numpy as np
import os
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore")  #The atypical formatting of the EyeMotions data results in a variety of inconsequential intake errors

def filterer(folder):
    ###Makes sure all files are there, and then passes to the next step
    csvList = os.listdir(folder)

    fCsvList = []
    for word in csvList:
        if ".csv" in word and "filtered" not in word:  #Checks that the file has not already been filtered
            inter = word[:-5]+"filtered.csv"
            if inter not in csvList:       
                fCsvList.append(word)
    
    for word in tqdm(fCsvList):
        fName = folder+word
        expName = fName[:-5] + "filtered2.csv"

        df = pd.read_csv(fName, usecols = [0]).to_numpy()
        
        for i,j in enumerate(df):
            if j == "#DATA":
                break
        
        i = i+2  #Establish where the header ends and data begins

        data = pd.read_csv(fName, skiprows = i, usecols=["Timestamp","ET_PupilLeft","ET_PupilRight"]).to_numpy()

        data = data[data[:,1]*0 == 0]  #Ensures no blank rows are included
        data = data[data[:,2]*0 == 0]
        
        A = filtering(data)
        df3 = A.returner()
        
        df3.to_csv(expName,index=False)
    

class filtering():
    def __init__(self, data):
        self.df = pd.DataFrame(data[:,0], columns = ["Timestamp"])
        self.data = data[:,1:3]
        self.size = np.shape(self.data)[0]
        
        self.lrmerge() #Averages left and right eye sizes into one column
        self.outliers() #Finds outliers via IQR and marks them for deletion
        self.crop()  #Actually deletes data that has been marked for deletion in the past steps
        
        self.find_blinks()  #Identifies blinks and blink borders from patterns in NaNIndex and adds them to NaNIndex
        self.crop()        
        
        if self.data[-1] * 0 != 0:
            self.data[-1] = np.nanmean(self.data)
        
        self.df["Pupil"] = self.data
        self.df["Pupil"] = self.df["Pupil"].interpolate(method = "pchip") #pchip was qualitatively the best and most consistent
        
        self.returner()
        
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
        upper_fence = quantile[3]+2.5*IQR
        lower_fence = quantile[1]-2.5*IQR
        
        self.NaNIndex = []
        for i,val in enumerate(self.data):
            if val < lower_fence or val > upper_fence:
                self.NaNIndex.append(i)
    
    
    def find_blinks(self):
        blink_start = []
        blink_stop = []
        cu = 0
        
        for i, NaN in enumerate(self.NaNIndex[:-1]):
            if NaN+1 == self.NaNIndex[i+1] and i < len(self.NaNIndex)-2:
                cu += 1
            else:
                if cu > 9 and cu < 100:
                    blink_stop.append(i)
                    blink_start.append(i-cu)
                cu = 0
                
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
            while self.onoCompare(pupil_val,ind+1):
                self.NaNIndex.append(ind)
                ind += 1
                pupil_val = self.data[ind]

    
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



    def returner(self):
        return(self.df)