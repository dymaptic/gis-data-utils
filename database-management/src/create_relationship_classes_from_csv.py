import arcpy, csv

# Define parameters for the script

# csv_file contains the values for the CreateRelationshipClass method. 
# The column headers should match the parameters from the CreateRelationshipClass method. 
# https://pro.arcgis.com/en/pro-app/tool-reference/data-management/create-relationship-class.htm
csv_file = r"..\sample_data\data_for_create_relationships.csv"

# The path to the geodatabase where the relationship class will be created
# If SDE, this should include the connection file path as well as the name of the database
geodatabase = r"<geodatabase connection file or file geodatabase>"

def CreateParametersList(parameterNames, parameterValues):
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
    
    create_relationship_class_parameters_list = list()

    # read csv
    print ("Opening " + csv_file + " to read relationships details")
    with open(csv_file, encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            # read column names in row 1 and store them in the create_relationship_class_parameters_list 
            if not create_relationship_class_parameters_list:
                create_relationship_class_parameters_list = row
            else:
                params = CreateParametersList(create_relationship_class_parameters_list, row)
                print ("Creating relationship class between tables {0} and {1}".format(row[0], row[1]))
                arcpy.CreateRelationshipClass_management(**params)
                print ("Completed creating relationship class between tables {0}".format(row[3]))

if __name__ == "__main__":
    main()