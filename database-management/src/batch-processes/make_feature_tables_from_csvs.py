import  arcpy, os
from builtins import csv
from os import listdir

# Define the parameters for the script

# csvs_folder contains a folder of csv files, each file containing parameters for the CreateFeatureClass method
# The column headers should match the parameters from the AddField method. 
# https://pro.arcgis.com/en/pro-app/tool-reference/data-management/add-field.htm
csvs_folder = r"..\sample_data\batch\make_feature_tables"

# The path to the geodatabase where the feature class will be created
# If SDE, this should include the connection file path as well as the name of the database
# geodatabase = r"<geodatabase connection file or file geodatabase>"
geodatabase = r"C:\Users\MaraStoica\Documents\ArcGIS\Default.gdb"

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


def main():
    # set overwrite to true
    arcpy.env.overwriteOutput = True

    # set workspace environment
    arcpy.env.workspace = geodatabase
    print ("Workspace environment set to " + arcpy.env.workspace)

    # loop through all files in the csvs_folder to create feature tables
    if os.path.exists(csvs_folder):
        for file in listdir(csvs_folder):
            fc_params = shared.GetParamsForFeatureClassFromCsvName(file)
            if fc_params:
                # create feature class
                print ("Creating feature class " + fc_params[0] + " in " + geodatabase )
                arcpy.CreateFeatureclass_management(geodatabase, fc_params[0], geometry_type=fc_params[1], spatial_reference=arcpy.SpatialReference(fc_params[2]))

                print ("Completed creating feature class")

                add_field_parameters_list = list()

                # read csv
                print ("Opening " + file + " to read fields")
                with open(file, encoding="utf-8-sig") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        # read column names in row 1 and store them in the addFieldParameters list
                        if not add_field_parameters_list:
                            add_field_parameters_list = row
                        else:
                            params = shared.CreateParametersForAddField(add_field_parameters_list, row)
                            arcpy.AddField_management(fc_params[0], **params)
                
                print ("Completed adding fields to feature class")

if __name__ == "__main__":
    main()