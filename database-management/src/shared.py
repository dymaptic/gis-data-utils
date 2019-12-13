def CreateParametersForAddField(parameterNames, parameterValues):
    parametersList = {}

    for value in parameterValues:
        if value is not None and value != '':
            index = parameterValues.index(value)
            parametersList[parameterNames[index]] = value 
    
    return parametersList

def GetParamsForFeatureClassFromCsvName(csv_file_name):
    # first make sure the file is a .csv
    if csv_file_name.endswith(".csv"):
        # get name of the file without extension
        csv_file_name.replace(".csv", "")
        # split file name on # to get parameters for CreateFeatureclass from file name
        fc_params = csv_file_name.split("#")
        if len(fc_params) == 3:
            if fc_params[1] in ["POINT", "MULTIPATCH", "MULTIPOINT", "POLYGON", "POLYLINE"]:
                return fc_params
    return None
            