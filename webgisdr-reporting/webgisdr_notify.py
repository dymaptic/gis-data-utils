"""=====================================================================================================================
Name: webgisdr_notify.py
Purpose:
    Script is meant to be called via command line, passing it the output JSON file from WebGISDR.
    It parses the results and creates a notification on a Slack channel.

Requirements:
    - ArcGIS Enterprise 11.0+ (the JSON output file doesn't exist at earlier versions)
    - Place script in the same directory as webgisdr.bat
    - Login to Slack (https://api.slack.com/apps) and connect/open your Workspace.
    - After login if Slack redirects you to another page, go back to https://api.slack.com/apps.
    - Click the "Create New App" button and select "From scratch".
    - Provide an app name such as "Webgisdr Notification", select your Workspace, and select "Create App".
    - Under Features, select "Incoming Webhooks", activate them.
    - Select "Add New Webhook to Workspace", choose the Slack Channel you want Notifications to appear, & select "Allow".
    - Copy the Webhook URL that is generated and keep it secret.
    - First time this script runs, hardcode the URL and assign it to the webhook_url Python variable.
    - Subsequently, change webhook_url back to an empty string so it's no longer in plain-text.

Author: Ed Conrad
Created: 12/18/2024
====================================================================================================================="""

import argparse
import json
import logging
import sys
import os

import keyring
import requests


def main():
    print('hello')
    log = os.path.join(os.path.dirname(__file__), "Webgisdr_Notify.log")
    logging.basicConfig(filename=log, level=logging.DEBUG, filemode='w',
                        format='%(asctime)s %(levelname)s %(message)s',
                        datefmt='%#m/%#d/%Y %#I:%M:%S %p')

    # command-line code
    parser = argparse.ArgumentParser(description='Python script parses the WebGISDR output JSON file and sends a '
                                                 'Notification to Slack.')
    parser.add_argument('--json_file', type=str,
                        help='The WebGISDR output JSON file.')
    args = parser.parse_args()
    json_file = args.json_file
    with open(json_file, 'r') as f:
        results = json.load(f)

    # TODO Instructions to user: First run only, provide the webhook_url in plain text. Subsequently, change it back to an empty string to keep it secret.
    webhook_url = ''
    service_name = 'Slack_Hook_WebGISDR_Notification'
    username = 'default'  # NOTE: keyring requires a username when saving a credential (we don't use this anywhere else)
    if webhook_url == '':
        # Retrieve URL from Windows Credential Store
        webhook_url = keyring.get_password(service_name=service_name, username=username)
    else:
        # Save URL to Windows Credential Store
        keyring.set_password(service_name=service_name, username=username, password=webhook_url)

    if webhook_url == '':
        logging.error('Unable to post notification - missing Slack Webhook URL.')
        sys.exit(1)

    # Data structure follows Slack's formatting https://api.slack.com/reference/surfaces/formatting
    payload = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"WebGISDR {results['operation'].upper()} {results['status'].upper()}\n"
                            f"Elapsed Time: {results['elapsedTime']}\nZip Time: {results['zipTime']}"
                    # "emoji": True
                }
            }
        ]
    }

    # Get detailed results of the various backup components: Portal, Data Store, each federated instance of ArcGIS Server
    for r in results['results']:
        new_section = {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*{r['name']}:*\n{r['URL']}\n{r['status'].upper()}\n{r['elapsedTime']}\n"
                }
            ]
        }
        payload['blocks'].append(new_section)

    response = requests.post(url=webhook_url, json=payload, headers={"Content-Type": "application/json"})
    if response.status_code == 200:
        logging.info('Successfully posted WebGISDR notification in Slack.')
    else:
        logging.error(f'Failed to post WebGISDR notification in Slack.\n{response.json()}')


if __name__ == '__main__':
    main()
