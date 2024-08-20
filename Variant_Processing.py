import os
import json
import pandas as pd
import numpy as np
from tqdm import tqdm

def process(time, data_folder, timestamp_folder, j_path):
    """
    

    Parameters
    ----------
    time : The amount of time kept from a given trial (In this case, the trial lengths averaged around 28 seconds, so the last 23 were kept and the first 5 were used to calculate baselines)
    path : The path of the folder containing the filtered data created in the previous step
    j_path : The path where the JSON will be exported to
    """
    
    data_path = os.listdir(data_folder)
    ref_path = os.listdir(timestamp_folder)
    
    indeces = []
    for i in ["L","A"]:
        for j in range(1,110):
            indeces.append(f"{j}{i}")
    
    df = pd.DataFrame(data = np.zeros([218,3]),  #Create a dataframe that stores whether or not a file was processed
                      index = indeces,
                      columns = ["Timestamp", "Data", "Total"])
    df["ID"] = indeces
    df['Exported?'] = pd.Series(dtype='int')

    csv_errs = []
    df['data_path'] = pd.Series(dtype='str')
    df['ref_path'] = pd.Series(dtype='str')
    for i,item in enumerate(data_path):
        if "filtered.csv" in item:
            if "Letter " in item:
                ID = item.split("_")[1].split("CE")[0]
                df["Data"][int(ID)-1] += 1
                df["data_path"][int(ID)-1] = data_folder+item
            elif "Arrow " in item:
                ID = item.split("_")[1].split("CE")[0]
                df["Data"][int(ID)+108] += 1
                df["data_path"][int(ID)+108] = data_folder+item
            else:
                csv_errs.append(item)
    for row in df["ID"]:
        num = row[:-1]
        letter = row[-1]
        if letter == "L":
            letter = "Letter"
        else:
            letter = "Arrow"
        for inter_row in ref_path:
            if letter in inter_row and "_"+num+"CE" in inter_row:
                df["ref_path"][row] = timestamp_folder+inter_row
                df["Timestamp"][row] +=1
                break
    
    for i in range(218):
        if df["Timestamp"][i] == 1 and df["Data"][i] == 1:
            df["Total"][i] = 1 
        else:
            df["Total"][i] = 0
    
    dictionary = {}
    for i in tqdm(range(np.shape(df)[0])): ###This for loop calls the calculations
        A = VariantProcess(df["ID"][i], df["data_path"][i], df["ref_path"][i], dictionary, seconds = time)
        dictionary = A.returner()

    with open(j_path, "w") as outfile:
        json.dump(dictionary, outfile, indent = 4)
    
    
    return df
    
    df = df[df["Total"] == 1]

class VariantProcess():
    def __init__(self, fileID, dataPath, referencePath, output, seconds = 0):
        try: ###I recognize these try and excepts are inelegant, but they are written so that erroneous prompts are still caught.  Try/Excepts are used more than is ideal during this segment due to the high possibility of errors in the data
            self.refdf = pd.read_csv(referencePath, usecols=["TrialISI","StimDur","arrow_disp.started"])
        except:
            self.refdf = pd.read_csv(referencePath, usecols=["TrialISI","StimDur","letter_disp.started"])
            
        self.refdf = self.refdf.to_numpy()
        self.data = pd.read_csv(dataPath, usecols = ["Timestamp","Pupil"]).to_numpy()
        
        self.output = output 
        
        self.startTrial = [0]
        self.endTrial = []
        
        for i,row in enumerate(self.refdf):
            if row[0]*0 != 0 and self.refdf[i-1,2]*0 == 0:
                self.startTrial.append(i+1)
                self.endTrial.append(i)
        
        self.newTrial = self.startTrial[:-1]
        
        self.errList = []
        err = 0

        try:
            self.baseline()
        except:
            err = 1
            self.errList.append(f"{dataPath} - baseline")
           
        self.numNames = []
        for i in self.newTrial:
            try:
                self.numName = str(int(self.refdf[i,0]))+" - " + str(int(self.refdf[i,1]))
            except:
                self.numName = str(int(self.refdf[i-5,0]))+" - " + str(int(self.refdf[i-5,1]))
            self.numNames.append(self.numName)
            
        self.startTimes = []
        self.endTimes = []
        self.fullTimes = []
        
        if seconds != 0:
            for k,endIndex in enumerate(self.endTrial):
                #print(endIndex)
                self.startTimes.append((self.refdf[endIndex-1,2]-seconds)*1000)
                self.endTimes.append((self.refdf[endIndex-1,2])*1000)
                self.fullTimes.append((self.refdf[self.newTrial[k],2])*1000)
        else:
            for k,endIndex in enumerate(self.endTrial):
                #print(endIndex)
                self.startTimes.append((self.refdf[self.newTrial[k],2])*1000)
                self.endTimes.append((self.refdf[endIndex-1,2])*1000)

        try:
            self.indeces = self.convertRef([self.startTimes,self.endTimes])
        except:
            err = 1
            print(dataPath)
            self.errList.append(f"{dataPath} - convertRef")
        
        if err == 0:
            self.output[fileID] = {"Dilated":{"750 - 800":[],"750 - 400":[],"750 - 200":[],"1000 - 800":[],"1000 - 400":[],"1000 - 200":[]},
                                   "BaselineAve":{"750 - 800":[],"750 - 400":[],"750 - 200":[],"1000 - 800":[],"1000 - 400":[],"1000 - 200":[]},
                                   "BaselineMax":{"750 - 800":[],"750 - 400":[],"750 - 200":[],"1000 - 800":[],"1000 - 400":[],"1000 - 200":[]},
                                   "TotalAve":{"750 - 800":[],"750 - 400":[],"750 - 200":[],"1000 - 800":[],"1000 - 400":[],"1000 - 200":[]},
                                   "TotalMax":{"750 - 800":[],"750 - 400":[],"750 - 200":[],"1000 - 800":[],"1000 - 400":[],"1000 - 200":[]},
                                   "TruncatedAve":{"750 - 800":[],"750 - 400":[],"750 - 200":[],"1000 - 800":[],"1000 - 400":[],"1000 - 200":[]},
                                   "TruncatedMax":{"750 - 800":[],"750 - 400":[],"750 - 200":[],"1000 - 800":[],"1000 - 400":[],"1000 - 200":[]},
                                   "Order":[]}  
            
            for i,j in enumerate(self.indeces):
                subsect = self.data[int(j[0]):int(j[1]),1]
                #subsectFull = self.data[int()]
                self.output[fileID]["Dilated"][self.numNames[i]].append(np.nanmean(subsect)-self.baseline[i])
                self.output[fileID]["BaselineAve"][self.numNames[i]].append(self.baseline[i])
                self.output[fileID]["TruncatedAve"][self.numNames[i]].append(np.nanmean(subsect))
                self.output[fileID]["BaselineMax"][self.numNames[i]].append(self.baselineMax[i])
                self.output[fileID]["TruncatedMax"][self.numNames[i]].append(np.nanmax(subsect))
        
            if seconds != 0:
                self.indecesFull = self.convertRef([self.fullTimes,self.endTimes])
                for i,j in enumerate(self.indecesFull):
                    subsect = self.data[int(j[0]):int(j[1]),1]
                    self.output[fileID]["TotalAve"][self.numNames[i]].append(np.nanmean(subsect))    
                    self.output[fileID]["TotalMax"][self.numNames[i]].append(np.nanmax(subsect))  

            comp1,comp2 = 0,0
            for val in self.refdf:
                #print(val)
                if val[0] != comp1 or val[1] != comp2:
                    if val[0]*0 == 0 and val[1]*0 == 0:
                        #print(val[:2])
                        self.output[fileID]["Order"].append(f"{int(val[0])} - {int(val[1])}")
                        comp1 = val[0]
                        comp2 = val[1]
        else:
            print(f"\033[31m{dataPath} skipped\033[0m")
    
    def baseline(self):
        self.baseline = []
        self.baselineMax = []
        for i in self.newTrial:
            endTime = 1000*self.refdf[i,2]
            startTime = endTime - 5000
            #print(f"{startTime} - {endTime}")
            j = 0
            while self.data[j,0] < startTime:
                j+=1
            startIndex = j
            j = 0
            while self.data[j+1,0] < endTime:
                j+=1
            endIndex = j
            self.baseline.append(np.nanmean(self.data[startIndex:endIndex,1:3]))
            self.baselineMax.append(np.nanmax(self.data[startIndex:endIndex,1:3]))
        #print(self.baseline)
        
    def convertRef(self, refIndeces):
        tempInd = np.zeros((len(refIndeces[0]),2))

        for i,array in enumerate(refIndeces):
            for k,index in enumerate(array):
                j = 0
                while self.data[j,0] < index:
                    j+=1
                under = j-1
                over = j
                if abs(self.data[under,0]-index) > abs(self.data[over,0]-index):
                    tempInd[k,i] = int(over)
                else:
                    tempInd[k,i] = int(under)
        return(tempInd)
    
    def returner(self):
        return(self.output)
    
    def errList(self):
        return(self.errList)