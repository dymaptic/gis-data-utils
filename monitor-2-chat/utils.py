"""=====================================================================================================================
Name: utils.py
Author: dymaptic (Kevin Sadrak)
Created: April 2024
Purpose: Utility methods and variables.
====================================================================================================================="""

import base64  # for creating the hash to validate the payload
import hashlib  # for creating the hash to validate the payload
import hmac
import psycopg2  # postgres module for connecting to the ArcGIS MonitorDB
import webhooksecrets as secrets
from typing import Union
import uuid
import os

images = {
    'Avatar': 'https://moraveclabsllc.maps.arcgis.com/sharing/rest/portals/self/resources/thumbnail1580303085740.png',
    'Error': 'https://moraveclabsllc.maps.arcgis.com/sharing/rest/content/items/29915b66728543b5bd6c7c3b82beb682/data',
    'Warning': 'https://moraveclabsllc.maps.arcgis.com/sharing/rest/content/items/2ac864c58f83488ebef5c4489bbd47dc/data',
}

def generateURLGUID():
    import webhooksecrets as secrets
    """Will check the secrets if a guid exists, if not it will make it, write it and return the value
    if it does exist it will return it"""
    webHookGuid = ""
    if hasattr(secrets, 'URL_GUID'):
        webHookGuid = secrets.URL_GUID
    else:
        print("generating a new guid")
        #create the item and return
        webHookGuid = str(uuid.uuid4())
        #write to the file.
        with open(os.path.join(os.path.dirname(__file__),"webhooksecrets.py"),"a") as secretFile:
            secretFile.write(f"\nURL_GUID='{theGUID}'")
        from importlib import reload
        secrets = reload(secrets)
    print()
    print("**********************************************************************************")
    print("paste the following url into your monitor notication webhook url")
    print(f"the webhook url is: http://127.0.0.1:5000/{webHookGuid}")
    print("if you have to change your hosts file or have a DNS name for this server the url will be:")
    print(f"the webhook url is: http://YOUR.CUSTOM.URL:5000/{webHookGuid}")
    print("**********************************************************************************")
    print()
        
    return webHookGuid

def queryAGMDB(query: str) -> Union[str, None]:
    """ Queries the ArcGIS Monitor Postgres DB and returns a value from the table or None. """

    value = None
    # connect to monitor:
    conn = psycopg2.connect(database=secrets.AGM_DB,
                            user=secrets.AGM_DB_USER,
                            host=secrets.AGM_DB_HOST,
                            password=secrets.AGMDBPASSWORD,
                            port=secrets.AGM_DB_PORT)
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    conn.commit()
    conn.close()
    for row in rows:
        value = row[0]
        break  # For completeness; however, note that all queries being past to this method currently have "LIMIT 1"
    del conn
    return str(value)


def verify_webhook(json_data, hmac_header):
    # Calculate HMAC

    digest = hmac.new(secrets.WEBHOOKSECRET.encode('utf-8'), json_data, digestmod=hashlib.sha256).digest()
    computed_hmac = base64.b64encode(digest)
    print(computed_hmac)

    return hmac.compare_digest(computed_hmac, hmac_header.encode('utf-8'))
