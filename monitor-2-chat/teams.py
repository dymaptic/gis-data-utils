"""=====================================================================================================================
Name: teams.py
Author: dymaptic (Kevin Sadrak)
Created: April 2024
Purpose: Webhook Messages with ArcGIS Monitor alerts to Microsoft Teams.

USAGE:
1. Refer to dymaptic blog article:  "ArcGIS Monitor 2023.3 Webhook Messages to your favorite chat software"
2. Populate values in webhooksecrets.py specific to your setup.
3. Then open cmd terminal and type the following:

python -m flask --app C:\webhooks\teams.py run --debug

====================================================================================================================="""

import hashlib
import hmac
import json

import pymsteams
from flask import Flask, request, abort

import webhooksecrets as secrets

from utils import queryAGMDB, images, verify_webhook,generateURLGUID
from importlib import reload

app = Flask(__name__)


domain_name = 'monitor.arcgis.dymaptic.com' #dont forget the port :)

# these are attributes from the webhook payload we don't want to show to the user in Teams (add/remove as desired).
EXCLUDED_ATTRIBUTES = ['id', 'opened_at', 'closed_at', 'state', 'observer_id', 'samples', 'status', 'aggregation',
                       'operator', 'warning_threshold', 'critical_threshold']

#check if there is a GUID to add to the url
webHookGuid = generateURLGUID()
print()
print("**********************************************************************************")
print("paste the following url into your monitor notication webhook url")
print(f"the webhook url is: http://127.0.0.1:5000/{webHookGuid}")
print("if you have to change your hosts file or have a DNS name for this server the url will be:")
print(f"the webhook url is: http://YOUR.CUSTOM.URL:5000/{webHookGuid}")
print("**********************************************************************************")
print()
secrets = reload(secrets)

@app.route(f'/{webHookGuid}', methods=['POST'])
def processPost():
    esriSHA = request.headers['X-Esrihook-Signature']
    bytes_data = request.get_data()  # This has to be called before
    

    secret = secrets.WEBHOOKSECRET.encode('utf-8')
    signature = 'sha256=' + hmac.new(secret, bytes_data,
                                     digestmod=hashlib.sha256).hexdigest()

    ##################################################
    # valid esri SHA with ours to verify the payload
    # if not hmac.compare_digest(signature,esriSHA):
    #    abort(401,description = 'Unable to Validate WebHook Secret.')

    data = json.loads(request.data)
    #print(data) #uncomment this to see the payload in the command line
    
    myTeamsMessage = pymsteams.connectorcard(secrets.TEAMS_WEBHOOK_URL)
    myTeamsMessage.title('ArcGIS Monitor Alert')

    alertSections = []

    for event in data['events']:

        # Optional for debugging/reporting
        # eventCount = len(data['events'])
        # messageText = f'{eventCount} new alerts have triggered in Monitor.<br>'

        # Filter new alerts that have been added to Postgres DB (each alert will have a section in the Teams card/post)
        if event['operation'] == 'add' and event['resource'] == 'alerts':

            ALERTID = event['attributes']['id']

            # Optional for debugging/reporting
            # NAME = event['attributes'].get('name', 'UNK')

            myTeamsMessage.color('#F8C471')
            alertSection = pymsteams.cardsection()
            alertSection.activityTitle(f'System Alert ID {ALERTID}')
            attributeTextList = []
            metricInfo = queryAGMDB(f"SELECT name FROM {secrets.AGM_DB_SCHEMA}.metrics WHERE id = {event['attributes']['metric_id']} LIMIT 1;")

            # Check status codes (3 == errors; 2 == warnings)
            if event['attributes']['status'] == 3:
                # use these dymaptic images or replace with your own!
                alertSection.activityImage(images['Error'])

                conditionText = f"<b>Reason</b>: {event['attributes']['aggregation']} {metricInfo} {event['attributes']['operator']} {event['attributes']['critical_threshold']}"
            else:
                # use these dymaptic images or replace with your own!
                alertSection.activityImage(images['Warning'])
                conditionText = f"<b>Reason</b>: {event['attributes']['aggregation']} {metricInfo} {event['attributes']['operator']} {event['attributes']['warning_threshold']}"

            # print all the info
            attributeTextList.append(conditionText)
            for attribute in event['attributes']:
                if attribute not in EXCLUDED_ATTRIBUTES:
                    value = 'None'

                    if attribute == 'metric_id':
                        # get the metric
                        value = metricInfo
                        # get the description and info
                        r_id = queryAGMDB(f"SELECT r_id FROM {secrets.AGM_DB_SCHEMA}.metrics WHERE id = {event['attributes'][attribute]} LIMIT 1;")
                        if r_id is not None:
                            value += ' - ' + queryAGMDB(f"SELECT description FROM {secrets.AGM_DB_SCHEMA}.metrics_registry WHERE r_id = '{r_id}' LIMIT 1;")
                    elif attribute == 'component_id':
                        # get the metric
                        value = queryAGMDB(f"SELECT name FROM {secrets.AGM_DB_SCHEMA}.components WHERE id = {event['attributes'][attribute]} LIMIT 1;")
                    elif event['attributes'][attribute]:
                        value = event['attributes'][attribute]
                    attributeTextList.append(f"<b>{attribute.title().replace('_', ' ')}</b>:   {value}")

            alertSection.activityText('<br>'.join(attributeTextList))
            alertSection.linkButton(f'View Alert {ALERTID}',
                                    f'https://{domain_name}/arcgis/monitor/alerts/{ALERTID}/overview ')

            alertSections.append(alertSection)

    myTeamsMessage.summary('Test Summary')
    myTeamsMessage.text(f'{len(alertSections)} new alerts have triggered in Monitor.')
    for section in alertSections:
        myTeamsMessage.addSection(section)

    # Only make POST to Teams if we actually have alerts
    if len(alertSections) > 0:
        myTeamsMessage.send()

    return 'OK'


@app.route(f'/{webHookGuid}', methods=['GET'])
def getHello():
    print('GET REQUEST')
    myTeamsMessage = pymsteams.connectorcard(secrets.TEAMS_WEBHOOK_URL)
    myTeamsMessage.title('ArcGIS Monitor Test Alert')
    
    myTeamsMessage.text(f'Test Alert from Monitor Webhook Translator')
    myTeamsMessage.send()
    print("Test Webhook Message sent to Teams.")
    return 'OK'


if __name__ == '__main__':
    app.run()
