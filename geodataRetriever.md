# Geodata Retriever ##

The Geodata Retriever is designed to download GIS data from the web and update the data you have in your database.  This will allow you to automate the process of keeping data up to date.

## Customize Script ##

This script can be customized to use with your specific data by entering a few fields.

* `dataName`: The name of the feature class to replace in your GDB or SDE.
* `downloadURL`: The url to the data to download.
* `saveFolder`: Path to the directory to donwload data into.
* `arcGIS Workspace`: Path to the GDB or SDE workspace. Inlcude the path to where the data in `dataName` is stored if there are internal folders.
* `toEmails`: List of emails to send error messages to if the script fails.
* `fromEmail`: Sender email.
* `fromEmailPassword`: Password to sender email.
* `server`: Email server to send from.

## Logging/Error Messages ##
The script includes error logging which will be saved to geodataRetriever.log in the folder where the script is run.  Emails will also be sent to the listed recipients if the script fails.

## Scheduling ##
To schedule the script, open Task Scheduler.  From the Action menu, choose Create Task. Give the task a name and optionally a description.

![image](https://user-images.githubusercontent.com/13741019/111682298-cd835c80-87e9-11eb-81ca-772f0de47c82.png)

On the Triggers tab, choose New and set the task to run as often as needed.

![image](https://user-images.githubusercontent.com/13741019/111683594-4e8f2380-87eb-11eb-9230-2b031d276982.png)

On the Action tab choose New.  For Action, choose Start a program.  In the Program/script field, browse to the python script. 

![image](https://user-images.githubusercontent.com/13741019/111683679-6bc3f200-87eb-11eb-8d86-befecb63269f.png)

Click OK to schedule the task.
