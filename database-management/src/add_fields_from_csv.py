import arcpy, csv

# Define parameters for the script

# csv_file contains the parameters for the AddFields method. 
# The column headers should match the parameters from the AddField method. 
# https://pro.arcgis.com/en/pro-app/tool-reference/data-management/add-field.htm
csv_file = r"..\sample_data\data_for_add_features.csv"

# The path to the feature class where the fields will be added 
# If SDE, this should include the connection file path as well as the name of the database
feature_class = r"<existing feature class>"

def CreateParametersForAddField(parameterNames, parameterValues):
    parametersList = {}

    for value in parameterValues:
        if value is not None and value != '':
            index = parameterValues.index(value)
            parametersList[parameterNames[index]] = value 
    
    return parametersList

def main():
    # set overwrite to true
    arcpy.env.overwriteOutput = True

    add_field_parameters_list = list()

    # read csv
    print ("Opening " + csv_file + " to read fields")
    with open(csv_file, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            # read column names in row 1 and store them in the addFieldParameters list
            if not add_field_parameters_list:
                add_field_parameters_list = row
            else:
                params = CreateParametersForAddField(add_field_parameters_list, row)
                arcpy.AddField_management(feature_class, **params)
    
    print ("Completed adding fields to feature class")

if __name__ == "__main__":
    main()