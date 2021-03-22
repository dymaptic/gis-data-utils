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

# Names of each feature class in gdb or sde to put data into - Keep these in the same order as downloadURLS
dataNames = ['RangeVegetationImprovement', 'FireOccurrenceLocations1984', 'OpiodCSV']
# URL of the download
downloadURLs = ['https://opendata.arcgis.com/datasets/0272be1853cc4bbf86b76df6581abeba_7.zip', 'https://opendata.arcgis.com/datasets/c57777877aa041ecaef98ff2519aabf6_60.zip', 'https://opendata.arcgis.com/datasets/e16768f13d084bb688120e6ddfbaa113_0.csv']
 # Save location
saveFolder = r'C:\Users\HeidiBinder-Vitti\Desktop\GeodataRetriever'
# GDB or SDE workspace - include path to where the data will be stored
arcGISWorkspace = r'C:\Users\HeidiBinder-Vitti\Desktop\GeodataRetriever\Map\Map.gdb'
# List of email recipeients
toEmails = ['heidi@dymaptic.com']
# Sender email
fromEmail = 'heidi@dymaptic.com'
# Password to sender email
fromEmailPassword = 'mqkfpwjwsfqdkftx'
# Email server
server = 'smtp.office365.com'

###########

def DownloadAndUnzip(url, saveLocation):
    # Download shapefile and save
    print("downloading data...")
    try:
        gcontext = ssl.SSLContext()
        data = urllib.request.urlopen(url, context=gcontext).read()
        with open(saveLocation, 'wb') as f:
            f.write(data)
    except Exception:
        logging.exception('Download Failed')
        SendEmail('Geodata Retriever failed', 'Data failed to download. ' + url + '\nSee log at ' + logFilePath + '\n'  + traceback.format_exc())
        sys.exit()

    if saveLocation.endswith('.zip'):
        print("unzipping...")
        try:
            with zipfile.ZipFile(saveLocation, 'r') as f:
                f.extractall(saveFolder)
        except Exception:
            logging.exception("Unzip failed")
            SendEmail('Geodata Retriever failed', 'Unzip failed.\nSee log at ' + logFilePath + '\n' + traceback.format_exc())
            sys.exit()

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

def UpdateFeatureClass(file, fcName):
    print("Updating data from " + file + " and " + fcName)

    # if CSV, get fields
    if file.endswith('.csv'):
        cols = []
        with open(file, encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            cols = next(reader)

        # Remove FID, OBJECTID
        fields = []
        for f in cols:
            if f != 'FID' and f != 'OBJECTID':
                f = re.sub(r'\W+', '_', f)
                fields.append(f) 

        # Check that all fields in csv are in target table
        fcFields = [f.name for f in arcpy.ListFields(fcName) if f.type != 'OID' and f.type != 'Geometry']
        if not set(fields).issubset(set(fcFields)):
            logging.error("Fields in CSV do not match fields in target table " + fcName)
            SendEmail('Geodata Retriever failed', "Fields in downloaded CSV do not match fields in target table" + fcName + "\nSee log at " + logFilePath)
            sys.exit()

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
            logging.error("Fields in shapefile do not match fields in target feature class " + fcName)
            SendEmail('Geodata Retriever failed', "Fields in download do not match fields in target feature class" + fcName + "\nSee log at " + logFilePath)
            sys.exit()

        # Add geometry field
        fields.append('SHAPE@')

    # Delete existing data from table if necessary
    print("deleting rows from " + fcName)
    try:
        arcpy.DeleteRows_management(fcName)
    except Exception:    
        logging.exception("Delete rows failed for " + fcName)
        SendEmail('Geodata Retriever failed', 'Delete rows failed for ' + fcName + '.\nSee log at ' + logFilePath + '\n' + traceback.format_exc())
        sys.exit()

    # Load data into Workspace
    print('loading data from ' + file)
    try:
        with arcpy.da.SearchCursor(file, fields) as sCursor:
            with arcpy.da.InsertCursor(fcName, fields) as inCursor:
                for row in sCursor:
                    inCursor.insertRow(row)
    except Exception:    
        logging.exception("Insert rows failed for " + fcName)
        SendEmail('Geodata Retriever failed', 'Insert data failed for ' + fcName + '.\nSee log at ' + logFilePath + '\n' + traceback.format_exc())
        sys.exit()

# Set up 
arcpy.env.workspace = arcGISWorkspace
logging.basicConfig(filename='geodataRetriever.log', level=logging.ERROR)
logFilePath = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'geodataRetriever.log')

# Check that dataNames and downloadURLs have equal lengths
if len(dataNames) != len(downloadURLs):
    logging.error("dataNames and DownloadURLs lists must be the same length.")
    SendEmail('Geodata Retriever failed', 'dataNames and DownloadURLs lists must be the same length.\nSee log at ' + logFilePath)
    sys.exit()

# Check for permissions to save directory
try:
    os.access(saveFolder, os.W_OK)
except Exception:
    logging.exception("Permission denied")
    SendEmail('Geodata Retriever failed', 'Permission denied to ' + saveFolder + '\nSee log at ' + logFilePath + '\n' + traceback.format_exc())
    sys.exit()

# Download and unzip all data
count = 0
for url in downloadURLs:
    if url.endswith('.zip'):
        saveLocation = os.path.join(saveFolder,'data.zip')
    elif url.endswith('.csv'):
        saveLocation = os.path.join(saveFolder, dataNames[count] + '.csv')
    DownloadAndUnzip(url, saveLocation)
    count += 1

# Get shapefile names
shapefiles = []
allfiles = []
for file in os.listdir(saveFolder):
    allfiles.append(os.path.join(saveFolder, file))

for f in allfiles:
    if f.endswith('.shp') or f.endswith('.csv'):
        shapefiles.append(f)

# sort by date
shapefiles.sort(key=os.path.getctime)

# For each shapefile downloaded, update feature class
count = 0
for s in shapefiles:
    UpdateFeatureClass(s, dataNames[count])
    count += 1

