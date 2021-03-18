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

########### User entered variables

# Name of feature class in gdb or sde
dataName = "RangeVegetationImprovement"
# URL of the download
downloadURL = 'https://opendata.arcgis.com/datasets/0272be1853cc4bbf86b76df6581abeba_7.zip'
 # Save location
saveFolder = r'C:\Temp'
# GDB or SDE workspace - include path to where the data will be stored
arcGISWorkspace = r'C:\Temp\Map\Map.gdb'
# List of email recipeients
toEmails = ['email1@dymaptic.com', 'email@gmail.com']
# Sender email
fromEmail = 'email@dymaptic.com'
# Password to sender email
fromEmailPassword = ''
# Email server
server = 'smtp.office365.com'

###########


# Set up 
saveLocation = os.path.join(saveFolder,'data.zip')
arcpy.env.workspace = arcGISWorkspace
logging.basicConfig(filename='geodataRetriever.log', level=logging.ERROR)
logFilePath = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'geodataRetriever.log')

# Get shapefile name
for file in os.listdir(saveFolder):
    if file.endswith(".shp"):
        shapefile = os.path.join(saveFolder, file)
print(shapefile)
# sys.exit()

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

# Check for permissions to save directory
try:
    os.access(saveFolder, os.W_OK)
except Exception:
    logging.exception("Permission denied")
    SendEmail('Geodata Retriever failed', 'Permission denied to ' + saveFolder + '\nSee log at ' + logFilePath + '\n' + traceback.format_exc())
    sys.exit()

# Download shapefile and save
print("downloading data...")
try:
    gcontext = ssl.SSLContext()
    data = urllib.request.urlopen(downloadURL, context=gcontext).read()
    with open(saveLocation, 'wb') as f:
        f.write(data)
except Exception:
    logging.exception('Download Failed')
    SendEmail('Geodata Retriever failed', 'Data failed to download. ' + downloadURL + '\nSee log at ' + logFilePath + '\n'  + traceback.format_exc())
    sys.exit()

print("unzipping...")
try:
    with zipfile.ZipFile(saveLocation, 'r') as f:
        f.extractall(saveFolder)
except Exception:
    logging.exception("Unzip failed")
    SendEmail('Geodata Retriever failed', 'Unzip failed.\nSee log at ' + logFilePath + '\n' + traceback.format_exc())
    sys.exit()

# Get field names 
shapefileFields = [f.name for f in arcpy.ListFields(shapefile) if f.type != 'OID' and f.type != 'Geometry']
fcFields = [f.name for f in arcpy.ListFields(dataName) if f.type != 'OID' and f.type != 'Geometry']

# Remove FID, OBJECTID
fields = []
for f in shapefileFields:
    if f != 'FID' and f != 'OBJECTID':
        fields.append(f)

# Check that all fields in shapefile are in target feature class
if not set(fields).issubset(set(fcFields)):
    logging.error("Fields in shapefile do not match fields in target feature class.")
    SendEmail('Geodata Retriever failed', "Fields in download do not match fields in target feature class.\nSee log at " + logFilePath)
    sys.exit()

# Add geometry field
fields.append('SHAPE@')

# Delete existing data from table if necessary
print("deleting rows from " + dataName)
try:
    arcpy.DeleteRows_management(dataName)
except Exception:    
    logging.exception("Delete rows failed")
    SendEmail('Geodata Retriever failed', 'Delete rows failed.\nSee log at ' + logFilePath + '\n' + traceback.format_exc())
    sys.exit()

# Load data into Workspace
print('loading data from ' + shapefileName)
try:
    with arcpy.da.SearchCursor(shapefile, fields) as sCursor:
        with arcpy.da.InsertCursor(dataName, fields) as inCursor:
            for row in sCursor:
                inCursor.insertRow(row)
except Exception:    
    logging.exception("Insert rows failed")
    SendEmail('Geodata Retriever failed', 'Insert data failed.\nSee log at ' + logFilePath + '\n' + traceback.format_exc())
    sys.exit()

