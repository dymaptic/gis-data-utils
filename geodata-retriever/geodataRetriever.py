import urllib.request
import ssl
import zipfile
import os
import sys
import arcpy
import logging
import smtplib
from email.message import EmailMessage
import traceback
import csv
import re


########### User entered variables

# Dictionary containing the feature class name from the GDB/SDE as key and download url as value
data = {
    'FeatureClassName': 'DownloadUrl',
    'RangeVegetationImprovement': 'https://opendata.arcgis.com/datasets/0272be1853cc4bbf86b76df6581abeba_7.zip'
}
# Save location
saveFolder = r'C:\Temp'
# GDB or SDE workspace - include path to where the data will be stored
arcGISWorkspace = r'C:\Temp\Map\Map.gdb'
# List of email recipeients
toEmails = ['email1@sample.com', 'email2@sample.com']
# Sender email
fromEmail = 'email@sample.com'
# Password to sender email
fromEmailPassword = ''
# Email server
server = 'smtp.office365.com'

###########


# Backup data
def Backup(backupFolder, fc):
    print('backing up data...')
    # create backup GDB if it doesn't exist
    if not os.access(backupFolder, os.W_OK):
        backup = arcpy.CreateFileGDB_management(saveFolder, 'Backup')
    # copy data into it - replace existing data
    fcdesc = arcpy.Describe(fc)
    backupFC = os.path.join(backupFolder, fcdesc.basename)
    if arcpy.Exists(backupFC):
        arcpy.Delete_management(backupFC)
    arcpy.Copy_management(fc, backupFC)

# Restore data from backup
def Restore(backupFolder, fc):
    print('restoring data...')
    fcdesc = arcpy.Describe(fc)
    backupFC = os.path.join(backupFolder, fcdesc.basename)
    fcPath = os.path.join(fcdesc.path, fc)
    arcpy.Delete_management(fc) # delete fc
    arcpy.Copy_management(backupFC, fcPath)  # copy backup of fc

# Download and unzip file
def DownloadAndUnzip(url, saveLocation, name):
    print("downloading data...")
    try:
        gcontext = ssl.SSLContext()
        data = urllib.request.urlopen(url, context=gcontext).read()
        with open(saveLocation, 'wb') as f:
            f.write(data)
    except Exception:
        print("ERROR: Download failed")
        logging.exception('Download Failed')
        SendEmail('Geodata Retriever failed', 'Data failed to download. ' + url + '\nSee log at ' + logFilePath + '\n'  + traceback.format_exc())
        return False

    if saveLocation.endswith('.zip'):
        print("unzipping...")
        try:
            with zipfile.ZipFile(saveLocation, 'r') as f:
                f.extractall(os.path.join(saveFolder, name))
        except Exception:
            print("ERROR: Unzip failed")
            logging.exception("Unzip failed")
            SendEmail('Geodata Retriever failed', 'Unzip failed.\nSee log at ' + logFilePath + '\n' + traceback.format_exc())
            return False
    return True

# Send email
def SendEmail(subject, message, TO = toEmails, FROM = fromEmail, password = fromEmailPassword, server = server):
    try:
        msg = EmailMessage()
        msg.set_content(message)
        msg['Subject'] = subject
        msg['To'] = ', '.join(TO)
        msg['From'] = FROM
        s = smtplib.SMTP(server, 587)
        s.ehlo()
        s.starttls()
        s.login(FROM, password)
        s.send_message(msg)
        s.quit()
    except Exception:
        logging.exception("Could not send email")

# Update data in ArcGIS Workspace
def UpdateFeatureClass(file, fcName):
    print("Updating feature class or table...")

    # if CSV, get fields
    if file.endswith('.csv'):
        cols = []
        with open(file, encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            cols = next(reader)

        # Remove FID, OBJECTID
        cols = [f for f in cols if len(f) != 0] # remove empty headers
        fields = []
        for f in cols:
            if f != 'FID' and f != 'OBJECTID' and not f[0].isdigit():
                f = re.sub('[^0-9a-zA-Z]+', '_', f)  # replace non-alphanumeric characters with underscore
                fields.append(f) 

        # Check that all fields in csv are in target table
        fcFields = [f.name for f in arcpy.ListFields(fcName) if f.type != 'OID' and f.type != 'Geometry']
        if not set(fields).issubset(set(fcFields)):
            print("ERROR: Fields in CSV do not match fields in target table")
            logging.error("Fields in CSV do not match fields in target table " + fcName)
            SendEmail('Geodata Retriever failed', "Fields in downloaded CSV do not match fields in target table" + fcName + "\nSee log at " + logFilePath)
            return

    # if SHP, get fields
    if file.endswith('.shp'):
        # Get field names 
        shapefileFields = [f.name for f in arcpy.ListFields(file) if f.type != 'OID' and f.type != 'Geometry']
        fcFields = [f.name for f in arcpy.ListFields(fcName) if f.type != 'OID' and f.type != 'Geometry']

        # Remove FID, OBJECTID
        fields = []
        for f in shapefileFields:
            if f != 'FID' and f != 'OBJECTID':
                fields.append(f)

        # Check that all fields in shapefile are in target feature class
        if not set(fields).issubset(set(fcFields)):
            print("ERROR: Fields in shapefile do not match fields in target feature class")
            logging.error("Fields in shapefile do not match fields in target feature class " + fcName)
            SendEmail('Geodata Retriever failed', "Fields in download do not match fields in target feature class" + fcName + "\nSee log at " + logFilePath)
            return

        # Add geometry field
        fields.append('SHAPE@')

    # Backup data
    Backup(backupFolder, fcName)

    # Delete existing data from table if necessary
    print("deleting rows... ")
    try:
        arcpy.DeleteRows_management(fcName)
    except Exception:    
        print("ERROR: Delete rows failed")
        logging.exception("Delete rows failed for " + fcName)
        SendEmail('Geodata Retriever failed', 'Delete rows failed for ' + fcName + '.\nSee log at ' + logFilePath + '\n' + traceback.format_exc())
        return

    # Load data into Workspace
    print('loading data...')
    try:
        with arcpy.da.SearchCursor(file, fields) as sCursor:
            with arcpy.da.InsertCursor(fcName, fields) as inCursor:
                for row in sCursor:
                    inCursor.insertRow(row)
    except Exception:    
        print("ERROR: Insert rows failed")
        logging.exception("Insert rows failed for " + fcName)
        SendEmail('Geodata Retriever failed', 'Insert data failed for ' + fcName + '.\nSee log at ' + logFilePath + '\n' + traceback.format_exc())
        Restore(backupFolder, fcName)
        return

# Set up 
arcpy.env.workspace = arcGISWorkspace
logging.basicConfig(filename='geodataRetriever.log', level=logging.ERROR)
logFilePath = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'geodataRetriever.log')
backupFolder = os.path.join(saveFolder, 'Backup.gdb')

# Check for permissions to save directory
try:
    os.access(saveFolder, os.W_OK)
except Exception:
    print("ERROR: Permission denied to save folder")
    logging.exception("Permission denied to " + saveFolder)
    SendEmail('Geodata Retriever failed', 'Permission denied to ' + saveFolder + '\nSee log at ' + logFilePath + '\n' + traceback.format_exc())
    sys.exit()

# For each data item, download data and udpate feature class or table
for d in data:
    print('Updating ' + d)
    # download data
    if data.get(d).endswith('.zip'):
        saveLocation = os.path.join(saveFolder, d + '.zip')
    elif 'csv' in  data.get(d):
        saveLocation = os.path.join(saveFolder, d + '.csv')
    else:
        saveLocation = os.path.join(saveFolder, d)
    success = DownloadAndUnzip(data.get(d), saveLocation, d)
    if success: 
        # get shp file names
        # NOTE: this will not work if multiple shapefiles are downloaded in the same zip
        if saveLocation.endswith('.zip'):
            files = []
            for file in os.listdir(os.path.join(saveFolder, d)):
                if file.endswith('.shp'):
                    files.append(os.path.join(saveFolder, d, file))
            if len(files) > 1:
                print("Cannot handle zip folder with multiple shapefiles.")
                logging.error("Cannot handle zip folder with multiple shapefiles.")
                SendEmail('Geodata Retriever failed', 'Cannot handle zip folder with multiple shapefiles.')
                sys.exit()
            saveLocation = files.pop()
        # update feature class
        UpdateFeatureClass(saveLocation, d)
