"""=====================================================================================================================
Name: discord.py
Author: dymaptic (Kevin Sadrak)
Created: April 2024
Purpose: Webhook Messages with ArcGIS Monitor alerts to Discord.

USAGE:
1. Refer to dymaptic blog article:  "ArcGIS Monitor 2023.3 Webhook Messages to your favorite chat software"
2. Populate values in webhooksecrets.py specific to your setup.
3. Then open cmd terminal and type the following:

python -m flask --app C:\webhooks\discord.py run --debug

====================================================================================================================="""

import hashlib
import hmac
import json

import requests
from flask import Flask, request, abort

import webhooksecrets as secrets

from utils import queryAGMDB, images, verify_webhook,generateURLGUID
from importlib import reload

app = Flask(__name__)


domain_name = 'monitor.arcgis.dymaptic.com'#dont forget the port :)

# these are attributes from the webhook payload we don't want to show to the user in Discord (add/remove as desired).
EXCLUDED_ATTRIBUTES = ['id', 'opened_at', 'closed_at', 'state', 'observer_id', 'samples', 'status', 'aggregation',
                       'operator', 'warning_threshold', 'critical_threshold']


#check if there is a GUID to add to the url
webHookGuid = generateURLGUID()
secrets = reload(secrets)

@app.route(f'/{webHookGuid}', methods=['POST'])
def processPost():
    #print(request.get_data(as_text=True, parse_form_data=True))
    #esriSHA = request.headers['X-Esrihook-Signature']
    #bytes_data = request.get_data()  # This has to be called before 
    # request.form
    #print(esriSHA)
    #secret = secrets.WEBHOOKSECRET.encode('utf-8')
    #signature = 'sha256=' + hmac.new(secret, bytes_data,
    #                                 digestmod=hashlib.sha256).hexdigest()

    #################################################
    # valid esri SHA with ours to verify the payload
    #if not hmac.compare_digest(signature, esriSHA):
    #    abort(401, description='Unable to Validate WebHook Secret.')

    data = json.loads(request.data)
    alertEmbeds = []

    for event in data['events']:
        
        # Optional for debugging/reporting
        # eventCount = len(data['events'])
        # messageText = f'{eventCount} new alerts have triggered in Monitor.<br>'

        # Filter new alerts that have been added to Postgres DB (each alert will have a section in the Discord card/post)
        if event['operation'] == 'add' and event['resource'] == 'alerts':
            ALERTID = event['attributes']['id']

            # Optional for debugging/reporting
            # NAME = event['attributes'].get('name', 'UNK')

            # create the header block / section
            alertSection = {'title': f'System Alert ID {ALERTID}', 'description': ''}
            attributeTextList = []
            metricInfo = queryAGMDB(f"SELECT name FROM {secrets.AGM_DB_SCHEMA}.metrics WHERE id = {event['attributes']['metric_id']} LIMIT 1;")

            # Check status codes (3 == errors; 2 == warnings)
            if event['attributes']['status'] == 3:
                alertSection['thumbnail'] = images['Error']
                alertSection['color'] = '13380395'
                conditionText = f"*Reason*: {event['attributes']['aggregation']} {metricInfo} {event['attributes']['operator']} {event['attributes']['critical_threshold']}"
            else:
                alertSection['thumbnail'] = images['Warning']
                alertSection['color'] = '15258703'
                conditionText = f"*Reason*: {event['attributes']['aggregation']} {metricInfo} {event['attributes']['operator']} {event['attributes']['warning_threshold']}"

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
                    attributeTextList.append(f"*{attribute.title().replace('_', ' ')}*:   {value}")

            alertSection['description'] = '\n'.join(attributeTextList)
            alertSection['url'] = f'\nhttps://{domain_name}/arcgis/monitor/alerts/{ALERTID}/overview '
            alertEmbeds.append(alertSection)

    # Only make POST to Discord if we actually have alerts
    if len(alertEmbeds) > 0:
        webHookData = {'content': f'ArcGIS Monitor Alert\nThere are {len(alertEmbeds)} new alerts',
                       'avatar_url': images['Avatar'],
                       'username': 'dymaptic ArcGIS Monitor',
                       'embeds': alertEmbeds}
        # print(data)
        response = requests.post(secrets.WEBHOOK_URL, json=webHookData)
        print(response.content)

    return 'OK'


@app.route(f'/{webHookGuid}', methods=['GET'])
def getHello():

    webHookData = {'content': f'Test Alert from Monitor Webhook Translator',
                   'username': 'dymaptic ArcGIS Monitor',
                   'avatar_url': images['Avatar']}
    response = requests.post(secrets.WEBHOOK_URL, json=webHookData)
    print("Test message sent.  Check discord for a test message!")

    return 'OK'


if __name__ == '__main__':
    app.run()
