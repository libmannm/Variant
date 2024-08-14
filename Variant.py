from Variant_Filter import filterer

path = "D:\\Research\\Kaiyo\\Code\\Variants\\Data\\" ##MAKE SURE TIMESTAMP FOLDER IS IN HERE
JSONPath = "D:\\Research\\Kaiyo\\Code\\Variants\\Variant_Final.json"
exportPath = "D:\\Research\\Kaiyo\\Code\\Variants\\Variant_Final.csv"


filterer(path)  ###Creates duplicates of each participant's data that has been reduced to the important features and processed (blinks etc.)
process(23, path, JSONPath) ###From the filtered data, assemble and calculate all interesting data; export into an intermediary JSON
VariantFinal(JSONPath, exportPath, data) ###Convert the JSON to a .csv for easier interpretation
