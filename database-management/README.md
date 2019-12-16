# Database Management Scripts 

All database management scripts use csv files as the source for the settings. This makes creating and re-creating feature classes and tables easier, especially during the initial phases of app development when schemas tend to change a lot. 

## Creating feature classes

Feature classes are geodatabase tables that have a shape associated with the data. There are two ways to create feature classes. You can use the standalone script to create just one feature class, or the batch option to create multiple feature classes. The csv files contain the parameters for the command as headers. See the `sample_data` folder for examples of csv files to use with the scripts. 

field_name | field_type	| field_length | field_alias
--- | --- | --- | ---
Project_Name  |  TEXT    | 100    | Project Name   |

**Creating single feature class**

The script `make_feature_table_from_csv.py` allows the user to create a feature class from a csv file. Modify the script with your path to the csv file, connection file, and feature class information

```python
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
```

**Creating multiple feature class**

The script `make_feature_tables_from_csvs.py` allows the user to create multiple feature classes from a folder containing csv files. The name of the feature class, geometry type, and spatial reference are retrieved from the name of the csv file. The following convention is implemented:

`feature_class_name#GEOMETRY#wkid.csv`

The name of the feature class, geometry type and spatial reference are separated by a `#`. The script parses the name of the csv file and retrieves the parameters. 

Example: `test_fc_1#POINT#4326.csv` will create a point feature class with the name `test_fc_1` and WGS84 (4326) spatial reference

Modify the script with your path to the csv file and connection file

```python
# Define the parameters for the script

# csvs_folder contains a folder of csv files, each file containing parameters for the CreateFeatureClass method
# The column headers should match the parameters from the AddField method. 
# https://pro.arcgis.com/en/pro-app/tool-reference/data-management/add-field.htm
csvs_folder = os.path.join(os.getcwd(), r"database-management\sample_data\batch\make_feature_tables")

# The path to the geodatabase where the feature classes will be created
# If SDE, this should include the connection file path as well as the name of the database
geodatabase = r"<geodatabase connection file or file geodatabase>"
```

## Creating standalone tables

Standalone tables are geodatabase tables that do not have a shape associated with the data. There are two ways to create standalone tables. You can use the standalone script to create just one standalone table, or the batch option to create multiple standalone tables. The csv files contain the parameters for the command as headers. See the `sample_data` folder for examples of csv files to use with the scripts. 

field_name | field_type	| field_length | field_alias
--- | --- | --- | ---
Project_Name  |  TEXT    | 100    | Project Name   |

**Creating single standalone table**

The script `make_standalone_table_from_csv.py` allows the user to create a standalone table from a csv file. Modify the script with your path to the csv file, connection file, and standalone table name

```python
# Define parameters for the script

# csv_file contains the parameters for the CreateTable method. 
# The column headers should match the parameters from the AddField method. 
# https://pro.arcgis.com/en/pro-app/tool-reference/data-management/add-field.htm
csv_file = r"..\sample_data\data_for_make_feature_table.csv"

# The path to the geodatabase where the standalone table will be created
# If SDE, this should include the connection file path as well as the name of the database
geodatabase = r"<geodatabase connection file or file geodatabase>"

# The name of the feature class to be created 
standalone_table_name = r"NEW_STANDALONE_TABLE"
```

**Creating multiple standalone tables**

The script `make_standalone tables_from_csvs.py` allows the user to create multiple standalone table from a folder containing csv files. The name of the standalone table, is retrieved from the name of the csv file. The following convention is implemented:

`test_table_1.csv` will result in a standalone table with the name `test_table_1`

Modify the script with your path to the csv file and connection file

```python
# Define the parameters for the script

# csvs_folder contains a folder of csv files, each file containing parameters for the CreateTable method
# The column headers should match the parameters from the AddField method. 
# https://pro.arcgis.com/en/pro-app/tool-reference/data-management/add-field.htm
csvs_folder = os.path.join(os.getcwd(), r"database-management\sample_data\batch\make_standalone_tables")

# The path to the geodatabase where the table will be created
# If SDE, this should include the connection file path as well as the name of the database
geodatabase = r"<geodatabase connection file or file geodatabase>"
```

## Creating relationships

Relationship creation is only available in batch mode using the `create_relationship_classes_from_csv.py script`. The csv file contains all the parameters for the command as headers. See the `sample_data` folder for an example csv file to use with the script. 

origin_table | destination_table | out_relationship_class | relationship_type | forward_label | backward_label | message_direction | cardinality | attributed | origin_primary_key | origin_foreign_key | destination_primary_key | destination_foreign_key
--- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---
TREES | INSPECTIONS | TREES_INSPECTIONS | COMPOSITE | INSPEACTIONS | TREES | NONE | ONE_TO_MANY | NONE | TREE_ID | TREE_ID |  |   



Modify the script with your path to the csv file and connection file

```python

# Define parameters for the script

# csv_file contains the values for the CreateRelationshipClass method. 
# The column headers should match the parameters from the CreateRelationshipClass method. 
# https://pro.arcgis.com/en/pro-app/tool-reference/data-management/create-relationship-class.htm
csv_file = r"..\sample_data\data_for_create_relationships.csv"

# The path to the geodatabase where the relationship class will be created
# If SDE, this should include the connection file path as well as the name of the database
geodatabase = r"<geodatabase connection file or file geodatabase>"
```