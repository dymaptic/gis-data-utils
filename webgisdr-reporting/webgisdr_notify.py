"""=====================================================================================================================
Name: webgisdr_notify.py
Purpose:
    Script parses the JSON results output file that WebGISDR.bat creates when it's run with an output file argument.
    It then sends a notification to either Teams or Slack depending on what has been configured.

Requirements:
    - ArcGIS Enterprise 11.0+ (the JSON output argument doesn't exist in earlier versions)
    - Place script in the same directory as webgisdr.bat
    - Setup Incoming Webhooks for Slack or Teams
    - Ensure that you have configured everything by updating values in config.json

Slack Instructions:
    - Login to Slack (https://api.slack.com/apps) and connect/open your Workspace.
    - After login if Slack redirects you to another page, go back to https://api.slack.com/apps.
    - Click the "Create New App" button and select "From scratch".
    - Provide an app name such as "WebGISDR Notification", select your Workspace, and select "Create App".
    - Under Features, select "Incoming Webhooks", activate them.
    - Select "Add New Webhook to Workspace", choose the Slack Channel you want Notifications to appear & select "Allow".
    - Copy the Webhook URL that is generated and put it in config.json
        - First time this script runs, this URL will be saved to Windows Credential Manager.
        - Subsequently, you could change the webhookURL value in config.json back to an empty string to keep it secret.

Teams Instructions:
    - Open Microsoft Teams.
    - In an existing Team, select Workflows from an existing channel.
    - Workflows will open and search for the "Post to a channel when a webhook request is received" template.
    - Give it a name such as "WebGISDR Notification", ensure that under connections, you are signed in and select Next.
    - After Details load, it will give you another opportunity to change which Team and Channel to post the
    notifications to. Select Add Workflow and a PowerAutomate Flow will be created.
    - Copy the Webhook URL that is generated and put it in config.json
        - First time this script runs, this URL will be saved to Windows Credential Manager.
        - Subsequently, you could change the webhookURL value in config.json back to an empty string to keep it secret.

Author: Ed Conrad
Created: 12/18/2024
====================================================================================================================="""

import json
import logging
import os
import traceback

import keyring
import requests


def main():
    script_dir = os.path.dirname(__file__)
    log = os.path.join(script_dir, "Webgisdr_Notify_Python.log")
    logging.basicConfig(filename=log, level=logging.INFO, filemode='w',
                        format='%(asctime)s %(levelname)s %(message)s',
                        datefmt='%#m/%#d/%Y %#I:%M:%S %p')
    config_file = os.path.join(script_dir, 'config.json')

    try:
        with open(config_file, mode='r') as file:
            config = json.load(file)
        python_config = config.get('pythonScriptSettings')
        shared_config = config.get('sharedSettings')

        chat = python_config.get('chatSoftware')
        if not chat or chat.lower() not in ('teams', 'slack'):
            raise ValueError('Missing or invalid chatSoftware value. Valid values include slack or teams.')

        chat = chat.lower()
        if chat == 'teams':
            service_name = 'Teams_Webhook_WebGISDR_Notification'
            username = 'Teams_webhook_default'  # NOTE: the keyring module requires a username when saving a credential.
        else:
            service_name = 'Slack_Webhook_WebGISDR_Notification'
            username = 'Slack_webhook_default'

        webhook_url = python_config.get('webhookURL')
        if not webhook_url:

            # Retrieve URL from Windows Credential Store
            webhook_url = keyring.get_password(service_name=service_name, username=username)
            if not webhook_url:
                raise ValueError('Unable to post notification - missing Webhook URL.')
        else:
            # Save URL to Windows Credential Store
            keyring.set_password(service_name=service_name, username=username, password=webhook_url)
            logging.info('Saved webhookURL to Windows Credential Store. You may set it to an empty string in the config '
                         'file and next time, it will be obtained using the keyring Python module.')

        # Place the WebGISDR results into the data structure expected by the chat software.
        results_file = shared_config.get('webgisdrResultsJsonFilename')
        if not results_file or not os.path.exists(results_file) or os.path.splitext(results_file)[1].lower() != '.json':
            raise ValueError("Missing or invalid path to the WebGISDR results JSON file. (i.e., the value of webgisdr.bat's --output parameter)")
        with open(results_file, mode='r') as file:
            results = json.load(file)

        if chat == 'teams':
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

        else:
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

        # Slack is returning 200 while Teams has been returning both 200 and 202.
        if 200 <= response.status_code < 300:
            logging.info(f'Successfully posted WebGISDR notification in {chat}.')
        else:
            logging.error(f'Failed to post WebGISDR notification in {chat}.\n{response.status_code}')

    except:
        logging.error(f'{traceback.format_exc()}')


if __name__ == '__main__':
    main()
