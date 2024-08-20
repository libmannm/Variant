import json
import pandas as pd
import numpy as np
from tqdm import tqdm

class VariantFinal():
    ### Most of this portion is formatting for the CSV
    def __init__(self, JSONPath, exportPath, data):
        f = open(JSONPath)
        self.data = json.load(f)
        
        key_del_list = []        
        for key in self.data.keys(): ###Another ultimately inelegant solution, but it works
            if self.data[key]["BaselineAve"]["750 - 800"] == [] or self.data[key]["BaselineAve"]["750 - 800"][0]*0 != 0:
                key_del_list.append(key)

        for key in key_del_list:
            del self.data[key]
        
        partList = list(self.data.keys())

        self.df = pd.DataFrame()
        
        self.initiate(len(partList))

        for i,part in tqdm(enumerate(partList)):
            trialList = self.data[part]["Order"]
            
            for j,trial in enumerate(trialList):
                idx = 6*i + j
                
                self.partID[idx] = part
                self.trialID[idx] = trial
                self.translate(part, trial, idx)
                self.delta(idx)
                
        self.convert()
        global df
        df = self.df
        df.to_csv(exportPath)
        
        exp_part = np.empty(np.shape(df)[0], dtype="<U10")
        for i in range(np.shape(df)[0]):
            exp_part[i] = str(self.df["Participant_Number"][i])+str(self.df["Letter_Code"][i])
        exp_part = np.unique(exp_part)
        #print(len(exp_part), exp_part)
        
        for i in exp_part:
            data["Exported?"][i] = 1
        data.to_csv(exportPath[:-4]+"_meta2.csv")
        
        global data2
        data2 = data[data["Exported?"] != 1]
        
    def convert(self):
        ###This portion is the manual conversion of each dictionary sub-array being converted to a column
        partInter = []
        partCodeInter = []
        ISIInter = []
        stimDurInter = []
        
        for i,partID in enumerate(self.partID):
            partInter.append(partID[:-1])
            partCodeInter.append(partID[-1:])
            ISIInter.append(self.trialID[i].split(" - ")[0])
            stimDurInter.append(self.trialID[i].split(" - ")[1])
            
            
        self.df["Participant_Number"] = partInter
        self.df["Letter_Code"] = partCodeInter
        self.df["Trial_ISI"] = ISIInter
        self.df["Stim_Duration"] = stimDurInter
    
        self.df["Baseline_Average"] = self.baselineAve
        self.df["Baseline_Max"] = self.baselineMax
        self.df["Total_Average"] = self.totalAve
        self.df["Total_Max"] = self.totalMax
        self.df["Truncated_Average"] = self.truncAve
        self.df["Truncated_Max"] = self.truncMax
    
        self.df["Average_Difference"] = self.aveDiff
        self.df["Maximum_Difference"] = self.maxDiff
    
    def initiate(self,partCt):
        count = partCt*6
        
        self.partID = np.empty(count, dtype = object)
        self.trialID = np.empty(count, dtype = object)

        self.baselineAve = np.zeros(count)
        self.baselineMax = np.zeros(count)
        self.truncAve = np.zeros(count)
        self.truncMax = np.zeros(count)
        self.totalAve = np.zeros(count)
        self.totalMax = np.zeros(count)
        
        self.aveDiff = np.zeros(count)
        self.maxDiff = np.zeros(count)
        
    def translate(self, part, trial, idx):
        self.baselineAve[idx] = self.data[part]["BaselineAve"][trial][0]
        self.baselineMax[idx] = self.data[part]["BaselineMax"][trial][0]
        self.truncAve[idx] = self.data[part]["TruncatedAve"][trial][0]
        self.truncMax[idx] = self.data[part]["TruncatedMax"][trial][0]
        self.totalAve[idx] = self.data[part]["TotalAve"][trial][0]
        self.totalMax[idx] = self.data[part]["TotalMax"][trial][0]
        
    def delta(self,idx):
        self.aveDiff[idx] = self.totalAve[idx] - self.baselineAve[idx]
        self.maxDiff[idx] = self.totalMax[idx] - self.baselineMax[idx]
