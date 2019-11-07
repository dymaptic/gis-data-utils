import arcpy, csv

# Define parameters for the script

# csv_file contains the parameters for the CreateFeatureClass method. 
# The column headers should match the parameters from the AddField method. 
# https://pro.arcgis.com/en/pro-app/tool-reference/data-management/add-field.htm
csv_file = r"..\sample_data\data_for_make_feature_table.csv"

# The path to the geodatabase where the feature class will be created
# If SDE, this should include the connection file path as well as the name of the database
geodatabase = r"<geodatabase connection file or file geodatabase>"

# The name of the feature class to be created 
feature_class_name = r"NEW_FEATURE_CLASS"

# The geometry type of the feature class. 
# Options are POINT, MULTIPATCH, MULTIPOINT, POLYGON, POLYLINE 
geometry_type = "POINT"

# The WKID of the spatial reference for the feature class
# 4326 is WGS 1984
wkid = 4326

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
    print ("Creating feature class " + feature_class_name + " in " + geodatabase )
    arcpy.CreateFeatureclass_management(geodatabase, feature_class_name, geometry_type=geometry_type, spatial_reference=arcpy.SpatialReference(wkid))

    print ("Completed creating feature class")

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
                arcpy.AddField_management(feature_class_name, **params)
    
    print ("Completed adding fields to feature class")

if __name__ == "__main__":
    main()