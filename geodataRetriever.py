import urllib.request
import ssl
import zipfile
import os
import arcpy
import logging
import smtplib
from email.message import EmailMessage

########### User entered variables

# Name of feature class in gdb
dataName = "RangeVegetationImprovement"
# Name of shapefile
shapefileName = 'Range_Vegetation_Improvement__Feature_Layer_'
# URL of the download
downloadURL = 'https://opendata.arcgis.com/datasets/0272be1853cc4bbf86b76df6581abeba_7.zip'
 # Save location
saveFolder = r'C:\Users\HeidiBinder-Vitti\Desktop\GeodataRetriever'
# GDB or SDE workspace
arcGISWorkspace = r'C:\Users\HeidiBinder-Vitti\Desktop\GeodataRetriever\Map\Map.gdb'
# List of email recipeients
toEmails = ['heidi@dymaptic.com']
# Sender email
fromEmail = 'heidi@dymaptic.com'
# Password to sender email
fromEmailPassword = ''
# Email server
server = 'smtp.office365.com'

###########


# Set up 
saveLocation = saveFolder + '\data.zip'
shapefile = saveFolder + '\\' + shapefileName + '.shp'
arcpy.env.workspace = arcGISWorkspace
logging.basicConfig(filename='geodataRetriever.log', level=logging.DEBUG)

def SendEmail(subject, message, TO = toEmails, FROM = fromEmail, password = fromEmailPassword, server = server):
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

# Check for permissions to save directory
try:
    os.access(saveFolder, os.W_OK)
except Exception as ex:
    logging.error('Permission denied: ' + ex)
    SendEmail('Geodata Retriever failed', 'Permission denied to ' + saveFolder)

# Download shapefile and save
print("downloading data...")
try:
    gcontext = ssl.SSLContext()
    data = urllib.request.urlopen(downloadURL, context=gcontext).read()
    with open(saveLocation, 'wb') as f:
        f.write(data)
except Exception as ex:
    logging.error('Download Failed: ' + ex)
    SendEmail('Geodata Retriever failed', 'Data failed to download. ' + downloadURL)

print("unzipping...")
try:
    with zipfile.ZipFile(saveLocation, 'r') as f:
        f.extractall(saveFolder)
except Exception as ex:
    logging.error("Unzip failed: " + ex)
    SendEmail('Geodata Retriever failed', 'Unzip failed.')

# Delete existing data from table if necessary
print("deleting rows from " + dataName)
try:
    arcpy.DeleteRows_management(dataName)
except Exception as ex:    
    logging.error("Delete rows failed: " + ex)
    SendEmail('Geodata Retriever failed', 'Delete rows failed.')

# Get field names 
shapefileFields = [f.name for f in arcpy.ListFields(shapefile)]
fcFields = [f.name for f in arcpy.ListFields(dataName)]

# Remove FID, OBJECTID, and SHAPE fields
fields = []
for f in shapefileFields:
    if f != 'FID' and f != 'OBJECTID' and not 'Shape' in f and not 'SHAPE' in f:
        fields.append(f)
fields.append('SHAPE@')

# Load data into Workspace
print('loading data from ' + shapefileName)
try:
    with arcpy.da.SearchCursor(shapefile, fields) as sCursor:
        with arcpy.da.InsertCursor(dataName, fields) as inCursor:
            for row in sCursor:
                inCursor.insertRow(row)
            del sCursor
            del inCursor
except Exception as ex:    
    logging.error("Insert rows failed: " + ex)
    SendEmail('Geodata Retriever failed', 'Insert data failed.')

