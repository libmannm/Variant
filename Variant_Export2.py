import pandas as pd

def variant_final(CSV_out, dictionary):
    ID_list = list(dictionary.keys())
    key_list = list(dictionary[ID_list[0]].keys())
    key_list.remove("key_order")
    
    #Columns
    participant_col = []
    letter_col = []
    ISI_col = []
    stim_col = []
    baseline_ave_col = []
    baseline_max_col = []
    total_ave_col = []
    total_max_col = []
    truncated_ave_col = []
    truncated_max_col = []
    average_diff_col = []
    max_diff_col = []
    
    for ID in ID_list:
        part_number = int(ID[:-1])
        letter_code = ID[-1]
        for key in key_list:
            print(key, key.split(" - "))
            ISI = int(key.split(" - ")[0])
            stimDur = int(key.split(" - ")[1])
            
            participant_col.append(part_number)
            letter_col.append(letter_code)
            ISI_col.append(ISI)
            stim_col.append(stimDur)
            
            baseline_ave_col.append(dictionary[ID][key]["Baseline_Ave"])
            baseline_max_col.append(dictionary[ID][key]["Baseline_Max"])
            total_ave_col.append(dictionary[ID][key]["Total_Ave"])
            total_max_col.append(dictionary[ID][key]["Total_Max"])
            truncated_ave_col.append(dictionary[ID][key]["Truncated_Ave"])
            truncated_max_col.append(dictionary[ID][key]["Truncated_Max"])
            average_diff_col.append(dictionary[ID][key]["Average_Difference"])
            max_diff_col.append(dictionary[ID][key]["Maximum_Difference"])
            
    df = pd.DataFrame(data = {"Participant":participant_col,
                              "Letter_Code": letter_col,
                              "Trial_ISI": ISI_col,
                              "Stim_Duration": stim_col,
                              "Baseline_Average": baseline_ave_col,
                              "Baseline_Maximum": baseline_max_col,
                              "Total_Average": total_ave_col,
                              "Total_Maximum": total_max_col,
                              "Truncated_Average": truncated_ave_col,
                              "Truncated_Maximum": truncated_max_col,
                              "Average_Difference": average_diff_col,
                              "Maximum_Difference": max_diff_col})
    
    df.to_csv(CSV_out, index = False)