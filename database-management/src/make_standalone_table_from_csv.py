import arcpy, csv

# Define parameters for the script

# csv_file contains the parameters for the CreateTable method. 
# The column headers should match the parameters from the AddField method. 
# https://pro.arcgis.com/en/pro-app/tool-reference/data-management/add-field.htm
csv_file = r"..\sample_data\data_for_make_feature_table.csv"

# The path to the geodatabase where the feature class will be created
# If SDE, this should include the connection file path as well as the name of the database
geodatabase = r"<geodatabase connection file or file geodatabase>"

# The name of the feature class to be created 
standalone_table_name = r"NEW_STANDALONE_TABLE"

def CreateParametersForAddField(parameterNames, parameterValues):
    parametersList = {}

    for value in parameterValues:
        if value is not None and value != '':
            index = parameterValues.index(value)
            parametersList[parameterNames[index]] = value 
    
    return parametersList

def main ():
    # set overwrite to true
    arcpy.env.overwriteOutput = True

    # set workspace environment
    arcpy.env.workspace = geodatabase
    print ("Workspace environment set to " + arcpy.env.workspace)

    # create feature class
    print ("Creating standalone table " + standalone_table_name + " in " + geodatabase )
    arcpy.CreateTable_management(geodatabase, standalone_table_name)

    print ("Completed creating standalone table")

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
                arcpy.AddField_management(standalone_table_name, **params)
    
    print ("Completed adding fields to standalone table")

if __name__ == "__main__":
    main()