import pandas as pd

def variant_final(CSV_out, dictionary):
    """
    Given data from the provided dictionary, this script reformats the relevant data into a dataframe.  Each participant is given 6 rows, one for each of the 6 variant tasks.  
    Each row is identified by the participant number, letter code, and two numbers which correspond to parameters of the variant tasks.

    Parameters
    ----------
    CSV_out : Path/name of the .csv where the data will be exported to
    dictionary : A dictionary (as per Variant_Processing2.py) containing the processed data to be exported
    """
    
    ID_list = list(dictionary.keys())
    key_list = list(dictionary[ID_list[0]].keys())
    key_list.remove("key_order")
    key_list.remove("Error")
    
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
    trial_error = []
    participant_error = []
    
    for ID in ID_list:
        part_number = int(ID[:-1])
        letter_code = ID[-1]
        for key in key_list:
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
            trial_error.append(dictionary[ID][key]["NaN_Rate"]["ratio"]*100)
            participant_error.append(dictionary[ID]["Error"]["Ratio"]*100)
            
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
                              "Maximum_Difference": max_diff_col,
                              "Trial_NaN": trial_error,
                              "Participant_NaN": participant_error})
    
    df.to_csv(CSV_out, index = False)