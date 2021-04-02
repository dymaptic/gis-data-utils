# Geodata Retriever ##

The Geodata Retriever is a tool built to download up to date geodata and replace that data in your GDB or SDE.  It works by downloading the latest version of your data, deleting the data currently in your feature class or table, and replacing it with the new data.  This tool can be scheduled to run as often as you'd like so your data is always up to date.

This tool works with shapefiles and CSV files.  It deletes the existing data in your feature class or table and replaces it with the downloaded data.  The tool also creates a backup of your data and replaces it if updating the data fails. The backup is deleted when the tool finishes.

If you run into any issues with this tool, create an issue in GitHub or email us at [info@dymaptic.com](mailto:info@dymaptic.com).

## Requirements ##

ArcGIS Pro or ArcGIS Server must be installed on your machine with a valid license in order to have Python3 and ArcPy available.

The tables and feature classes you want to update cannot be opened at the time you run this tool.  If any of the data sources are open the script will exit.

When choosing data to download make sure that only one shapefile is downloaded at a time or the tool will fail.

## Customize ##

To use this tool, download [geodataRetriever.py](https://github.com/dymaptic/gis-data-utils/blob/7b60d8f03b35c432b96a3a8c1b4373f5e07ee230/geodata-retriever/geodataRetriever.py) and open it in a text editor. Eenter values in the user entered variable section at the top of the tool.

* `data`: A dictionary with the key as the name of the feature class to replace in your GDB or SDE. Value is the url to the data to download.

        ```
        data = {
            'key':'value',
            'FeatureClassName':'Url to download shapefile',
            'TableName':'Url to download CSV file'
        }
        ```
* `saveFolder`: Path to the directory to donwload data into. Example: `r'C:\Temp'`.  The `r` before the quotes is needed to enter a file path.
* `arcGIS Workspace`: Path to the GDB or SDE workspace. Inlcude the path to where the data in `dataName` is stored if there are internal folders. Example: `r'C:\Temp\Map\Map.gdb'` or `r'C:\Temp\Map\Map.sde\FolderName'`
* `toEmails`: A list of emails to send error messages to if the script fails. Example: `['email@gmail.com']` or `['email@gmail.com', 'email2@yahoo.com']`
* `fromEmail`: Sender email. Example: `'myEmail@gmail.com'`
* `fromEmailPassword`: Password to fromEmail. Example: `'password'`
* `server`: Email server to send from.  For example, to send emails from a gmail account use '`'smtp.gmail.com'`.  To send from outlook use `'smtp.office365.com'`.

## Logging/Error Messages ##

The tool includes error logging which will be saved to `geodataRetriever.log` in the folder where the script is run.  Emails will also be sent to the listed recipients if the tool fails.

## Run Tool ##

You may want to run the tool to make sure everything works correctly before scheduling it to run automatically. To do so, open a Command Prompt.  To start the Python3 environment, enter `"%PROGRAMFILES%\ArcGIS\Pro\bin\Python\Scripts\proenv"` and hit enter. Next you enter `python C:\Path to tool\geodataRetriever.py` and hit enter to run the program.  This will begin the tool.

Additional information about running a Python script using ArcGIS Pro can be found [here](https://pro.arcgis.com/en/pro-app/latest/arcpy/get-started/installing-python-for-arcgis-pro.htm).

## Scheduling ##
To schedule the tool, open Task Scheduler.  From the Action menu, choose Create Task. Give the task a name and optionally a description.

![image](https://user-images.githubusercontent.com/13741019/111682298-cd835c80-87e9-11eb-81ca-772f0de47c82.png)

On the Triggers tab, choose New and set the task to run as often as needed.

![image](https://user-images.githubusercontent.com/13741019/111683594-4e8f2380-87eb-11eb-9230-2b031d276982.png)

On the Action tab choose New.  For Action, choose Start a program.  In the Program/script field, browse to the python script. 

![image](https://user-images.githubusercontent.com/13741019/111683679-6bc3f200-87eb-11eb-8d86-befecb63269f.png)

Click OK to schedule the task.
