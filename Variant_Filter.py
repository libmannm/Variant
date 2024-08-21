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

    print(len(fCsvList))
    
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
        
        self.blinkOnOff() #Defines what qualifies as a blink and notes where they are in a variety of ways
        self.monotonic() #monotonically filters the beginning and ends of the blinks in a form of noise based filtering
        self.crop() #Actually deletes data that has been marked for deletion in the past steps       
        
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
        
    def crop(self):
        for j in self.NaNIndex:
            self.data[j] = np.nan
        
        self.NaNIndex = np.sort(self.NaNIndex)
        
    
    def blinkOnOff(self):
        self.OnBlink = []
        self.OffBlink = []
        self.blinkIndex = []

        if len(self.NaNIndex) == 0:
            return 0
        
        k = self.NaNIndex[0]-1 #Just a starting value
        counter = 0
        
        for j in self.NaNIndex:
            #go through each NaN value, if it is consecutive, then increase the current value. If not, append the old value to self.blinkIndex and set the counter to 0
            if (j-k)==1:
                counter += 1
            else:
                self.blinkIndex.append(counter+1)
                counter = 0
            k = j
        self.blinkIndex[0] = self.blinkIndex[0]-1 #accounts for autostarting the first value (k)   
        
        i = 0
        self.blinkIndexCu = []
        for j in self.blinkIndex:
            #creates values of the cumulative starting points of each consecutive period of NaN Values, which is used for locating
            i += j
            self.blinkIndexCu.append(i)
        self.blinkIndexCu.insert(0,0) #allows to be 0 indexed
        
        for j,k in enumerate(self.blinkIndex):
            # if NaN values last for between ~45 and ~500 ms, their start and end point indeces are recorded
            if k > 9 and k<100:
                self.OnBlink.append(self.NaNIndex[k]-1)
                self.OffBlink.append(self.NaNIndex[self.blinkIndexCu[j+1]-1]+1)

    def monoCompare(self,first,second):
        if first > self.data[second]:
            return False
        elif second+1 == len(self.data):
            return False
        else:
            return True

    def monotonic(self):
        #dending on on or offset, it goes back until it finds a value that isnt NaN and is larger or smaller than the initial on or offset
        #onsets
        for j in range(len(self.OnBlink)):    
            ind = self.OnBlink[j]
            indP = self.data[ind]
            while self.monoCompare(indP,ind-1):
                self.data[ind] = np.nan
                ind = ind - 1
                indP = self.data[ind]
            self.OnBlink[j] = ind
        
        #offsets
        for j in range(len(self.OffBlink)):
            ind = self.OffBlink[j]
            indP = self.data[ind]
            while self.monoCompare(indP, ind+1):
                self.data[ind] = np.nan
                ind += 1
                indP = self.data[ind]
            self.OffBlink[j] = ind

    def returner(self):
        return(self.df)