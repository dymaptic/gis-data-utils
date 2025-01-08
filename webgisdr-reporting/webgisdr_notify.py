"""=====================================================================================================================
Name: webgisdr_notify.py
Purpose:
    Script is meant to be called via command line, passing it the output JSON file from WebGISDR.
    It parses the results and creates a notification on a Slack channel.

Requirements:
    - ArcGIS Enterprise 11.0+ (the JSON output argument doesn't exist at earlier versions)
    - Place script in the same directory as webgisdr.bat
    - Setup Incoming Webhooks for Slack or Teams

Slack Instructions:
    - Login to Slack (https://api.slack.com/apps) and connect/open your Workspace.
    - After login if Slack redirects you to another page, go back to https://api.slack.com/apps.
    - Click the "Create New App" button and select "From scratch".
    - Provide an app name such as "WebGISDR Notification", select your Workspace, and select "Create App".
    - Under Features, select "Incoming Webhooks", activate them.
    - Select "Add New Webhook to Workspace", choose the Slack Channel you want Notifications to appear & select "Allow".
    - Copy the Webhook URL that is generated and keep it secret.
        - First time this script runs, hardcode the URL and assign it to the webhook_url Python variable.
        - Subsequently, change webhook_url back to an empty string, so it's no longer in plain-text.

Teams Instructions:
    - Open Microsoft Teams.
    - In an existing Team, select Workflows from an existing channel.
    - Workflows will open and search for the "Post to a channel when a webhook request is received" template.
    - Give it a name such as "WebGISDR Notification", ensure that under connections, you are signed in and select Next.
    - After Details load, it will give you another opportunity to change which Team and Channel to post the
    notifications to. Select Add Workflow and a PowerAutomate Flow will be created.
    - Copy the Webhook URL and place it into the webgisdr_notify.py script.
        - First time this script runs, hardcode the URL and assign it to the webhook_url Python variable.
        - Subsequently, change webhook_url back to an empty string, so it's no longer in plain-text.

Author: Ed Conrad
Created: 12/18/2024
====================================================================================================================="""

import argparse
import json
import logging
import os
import sys
import traceback

import keyring
import requests


def main():
    log = os.path.join(os.path.dirname(__file__), "Webgisdr_Notify_Python.log")
    logging.basicConfig(filename=log, level=logging.INFO, filemode='w',
                        format='%(asctime)s %(levelname)s %(message)s',
                        datefmt='%#m/%#d/%Y %#I:%M:%S %p')
    try:
        # command-line code
        parser = argparse.ArgumentParser(description='Python script parses the WebGISDR output JSON file and sends a '
                                                     'Notification to Slack.')
        parser.add_argument('--json_file', type=str,
                            help='The WebGISDR output JSON file.')
        parser.add_argument('--chat_software', type=str,
                            help='The location where the notification will go. Valid values are teams and slack.')
        args = parser.parse_args()
        json_file = args.json_file
        with open(json_file, 'r') as f:
            results = json.load(f)

        chat = args.chat_software
        if chat is None or chat.lower() not in ('slack', 'teams'):
            raise ValueError('Invalid value provided for chat_software argument. Valid values include slack or teams.')

        if chat.lower() == 'teams':
            service_name = 'Teams_Webhook_WebGISDR_Notification'
            username = 'Teams_webhook_default'  # NOTE: the keyring module requires a username when saving a credential.
        elif chat.lower() == 'slack':
            service_name = 'Slack_Webhook_WebGISDR_Notification'
            username = 'Slack_webhook_default'

        # TODO Instructions to user:
        # - First run only, provide the webhook_url in plain text.
        # - Subsequently, change it back to an empty string to keep it secret.
        webhook_url = ''
        if webhook_url == '':
            # Retrieve URL from Windows Credential Store
            webhook_url = keyring.get_password(service_name=service_name, username=username)
        else:
            # Save URL to Windows Credential Store
            keyring.set_password(service_name=service_name, username=username, password=webhook_url)

        if webhook_url == '':
            logging.error('Unable to post notification - missing Webhook URL.')
            sys.exit(1)

        payload = {}
        if chat.lower() == 'teams':
            payload = {
                "type": "message",
                "attachments": [
                    {
                        "contentType": "application/vnd.microsoft.card.adaptive",
                        "contentUrl": None,
                        "content": {
                            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                            "type": "AdaptiveCard",
                            "version": "1.2",
                            "body": [
                                {
                                    "type": "TextBlock",
                                    "size": "large",
                                    "weight": "bolder",
                                    "text": "WebGISDR Summary"
                                },
                                {
                                    "type": "FactSet",
                                    "facts": []
                                }
                            ]
                        }
                    }
                ]
            }

            overall_summary = payload['attachments'][0]['content']['body'][1]['facts']

            # Create facts for the overall result
            overall_summary.extend([
                {'title': 'Overall Result', 'value': results['status']},
                {'title': 'Elapsed Time', 'value': results['elapsedTime']},
                {'title': 'Zip Time', 'value': results['zipTime']}
            ])

            for r in results['results']:
                payload['attachments'][0]['content']['body'].append({
                                    "type": "TextBlock",
                                    "size": "medium",
                                    "weight": "bolder",
                                    "text": r['name']
                                })
                payload['attachments'][0]['content']['body'].append({
                                    "type": "FactSet",
                                    "facts": [{'title': 'URL', 'value': r['URL']},
                                              {'title': 'Result', 'value': r['status']},
                                              {'title': 'Elapsed Time', 'value': r['elapsedTime']}]
                                })

        elif chat.lower() == 'slack':
            # Slack's data structure formatting https://api.slack.com/reference/surfaces/formatting
            payload = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "WebGISDR Summary"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Overall Result:* {results['status']}\n"
                                        f"Elapsed Time: {results['elapsedTime']}\n"
                                        f"Zip Time: {results['zipTime']}\n"
                            }
                        ]
                    }
                ]
            }

            # Get results of the various backup components: Portal, Data Store, each federated instance of ArcGIS Server
            for r in results['results']:
                new_section = {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*{r['name']}:*\n"
                                    f"{r['URL']}\n"
                                    f"Result: {r['status']}\n"
                                    f"Elapsed Time: {r['elapsedTime']}\n"
                        }
                    ]
                }
                payload['blocks'].append(new_section)

        response = requests.post(url=webhook_url, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        if response.status_code == 200:
            logging.info(f'Successfully posted WebGISDR notification in {chat}.')
        else:
            logging.error(f'Failed to post WebGISDR notification in {chat}.\n{response.json()}')

    except:
        logging.error(f'\n{traceback.format_exc()}')


if __name__ == '__main__':
    main()
