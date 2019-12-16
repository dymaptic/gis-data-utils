import  arcpy, os, csv
from os import listdir

# Define the parameters for the script

# csvs_folder contains a folder of csv files, each file containing parameters for the CreateTable method
# The column headers should match the parameters from the AddField method. 
# https://pro.arcgis.com/en/pro-app/tool-reference/data-management/add-field.htm
csvs_folder = os.path.join(os.getcwd(), r"database-management\sample_data\batch\make_standalone_tables")

# The path to the geodatabase where the table will be created
# If SDE, this should include the connection file path as well as the name of the database
#geodatabase = r"<geodatabase connection file or file geodatabase>"
geodatabase = r"C:\Users\MaraStoica\Documents\ArcGIS\Default.gdb"

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

    # set workspace environment
    arcpy.env.workspace = geodatabase
    print ("Workspace environment set to " + arcpy.env.workspace)

    # loop through all files in the csvs_folder to create standalone tables
    if os.path.isdir(csvs_folder):
        for file in listdir(csvs_folder):
            # create standalone table
            standalone_table_name = file.replace(".csv", "")

            print ("Creating standalone table" + standalone_table_name + " in " + geodatabase )
            arcpy.CreateTable_management(geodatabase, standalone_table_name)

            print ("Completed creating standalone table")

            add_field_parameters_list = list()

            # read csv
            file_path = os.path.join(csvs_folder, file)
            print ("Opening " + file_path + " to read fields")
            with open(file_path, encoding="utf-8-sig") as f:
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